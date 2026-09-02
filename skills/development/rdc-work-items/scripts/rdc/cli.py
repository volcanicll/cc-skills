# -*- coding: utf-8 -*-
"""研发云工作项自动化 CLI（配置驱动，所有环境变量可在 rdc-config.yaml 自定义）

纯标准库运行（无需 pip 安装依赖）。状态流转走 updateWorkItems/edit 接口。

用法：
  python -m rdc.cli setup-config                       # 首次配置向导（写全局配置）
  python -m rdc.cli doctor                             # 环境自检（配置/鉴权/调试端口/git 仓库）
  python -m rdc.cli --config rdc-config.yaml auth      # 提取鉴权（自动发现/自动启动浏览器）
  python -m rdc.cli auth --manual                      # 手动粘贴 Cookie 兜底
  python -m rdc.cli stats --since 2026-08-01 --until 2026-08-31 -o commits.json
  python -m rdc.cli build-excel -i work_items.json -o 营销域8月-示例.xlsx
  python -m rdc.cli prepare 营销域8月-示例.xlsx -o 导入-新建.xlsx --status 新建
  python -m rdc.cli validate 导入-新建.xlsx            # 只读校验（导入前建议先跑）
  python -m rdc.cli import 导入-新建.xlsx --yes         # 导入（默认需确认，--yes 跳过）
  python -m rdc.cli export -o 导出.xlsx --since 2026-08-01 --until 2026-08-31
  python -m rdc.cli update-status 导出.xlsx --status 处理中 --dry-run   # 接口流转（先 dry-run）
  python -m rdc.cli update-status --ids P22TEST0000001-6864 --status 已完成
  python -m rdc.cli flow --src 营销域8月-示例.xlsx --mode full    # 全流程（默认 dry-run，--yes 执行）
  python -m rdc.cli flow --mode import --yes           # 只创建（编号保存到 out-dir/ids.json）
  python -m rdc.cli flow --mode status --yes           # 只流转（读取 out-dir/ids.json 或 --ids）
  python -m rdc.cli --version
"""
import argparse
import getpass
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rdc import __version__, api, auth, config, doctor, excelgen, prepare, stats


def _cfg(args):
    return config.load_config(getattr(args, "config", None))


def _auth_path(args):
    return _cfg(args).get("auth_file", "auth.json")


def _is_placeholder(v):
    """是否为空 / 未配置占位符（YOUR_*）。"""
    return v is None or str(v).strip() == "" or str(v).strip().startswith("YOUR_")


def _missing_fields(cfg, fields):
    """返回仍缺失（空/占位符）的 (key, label) 列表。"""
    return [(k, l) for k, l in fields if _is_placeholder(cfg.get(k))]


def _merge_auth_into_cfg(cfg):
    """把已获取的登录信息（auth.json）回填到配置中缺失的平台字段。"""
    path = cfg.get("auth_file", "auth.json")
    if not os.path.exists(path):
        return cfg
    try:
        a = auth.load_auth(path)
    except Exception:
        return cfg
    headers = a.get("headers", {}) or {}
    for key, val in (("assignee_emp_no", a.get("emp_no")),
                     ("project_id", a.get("project_id")),
                     ("team_id", a.get("team_id")),
                     ("tenant_id", headers.get("x-tenant-id")),
                     ("api_key", headers.get("x-api-key"))):
        if val and _is_placeholder(cfg.get(key)) and not _is_placeholder(val):
            cfg[key] = val
    return cfg


def _confirm(question, default=False):
    """自然语言确认；非交互（无终端）时不执行任何操作。"""
    if not sys.stdin.isatty():
        return False
    hint = "[Y/n] " if default else "[y/N] "
    ans = input(f"{question} {hint}").strip().lower()
    if ans in ("y", "yes"):
        return True
    if ans in ("n", "no"):
        return False
    return default


def _save_runtime_config(cfg, source="本次补充的信息"):
    """把运行期收集的配置写入全局配置（多平台路径），避免下次重复输入。"""
    data = dict(cfg)
    data.pop("auth_file", None)
    home = os.path.expanduser("~")
    cd = data.get("chrome_profile_dir", "")
    if isinstance(cd, str) and cd.startswith(home + os.sep):
        data["chrome_profile_dir"] = "~" + cd[len(home):]
    path = config.global_config_path()
    config.write_global_config(data, path)
    print(f"✅ {source}已保存到全局配置 {path}")


def _ask_fields(cfg, fields):
    """交互式自然语言收集缺失字段，返回更新后的 cfg。"""
    for key, label in fields:
        cur = cfg.get(key, "")
        if key == "api_key":
            raw = getpass.getpass(f"  {label}（{key}）: ").strip()
        else:
            raw = input(f"  {label}（{key}）[{cur}]: ").strip()
        if raw:
            cfg[key] = raw
    return cfg


PLATFORM_FIELDS = [
    ("workspace", "工作区"),
    ("project_id", "项目 ID"),
    ("team_id", "团队 ID"),
    ("tenant_id", "租户 ID"),
    ("api_key", "API Key"),
    ("assignee_emp_no", "员工号"),
    ("assignee_name", "姓名"),
    ("team_name", "团队名称"),
]

EXCEL_INFO_FIELDS = [
    ("assignee_name", "姓名（指派给/创建人列）"),
    ("team_name", "团队名称（团队列）"),
]


def _ensure_config(args, cfg, fields, reason):
    """确保所需配置齐全：先回填已获取的登录信息，缺失项再向用户询问。

    - 交互终端：逐个以自然语言询问补充，并可保存为全局配置；
    - 非交互环境：用自然语言列出缺失项并退出，由使用者补充后重试。
    """
    cfg = _merge_auth_into_cfg(cfg)
    missing = _missing_fields(cfg, fields)
    if not missing:
        return cfg
    if sys.stdin.isatty():
        print(f"\n还缺少以下信息（用于{reason}），请补充：")
        _ask_fields(cfg, missing)
        still = _missing_fields(cfg, fields)
        if still:
            raise SystemExit("仍缺少必要配置："
                             + "、".join(f"{l}（{k}）" for k, l in still)
                             + "。请补充后重试。")
        if _confirm("是否将本次补充的信息保存为全局配置，避免下次重复输入？", default=True):
            _save_runtime_config(cfg)
        return cfg
    raise SystemExit("缺少以下信息：" + "、".join(f"{l}（{k}）" for k, l in missing)
                     + f"。{reason}需要这些信息，请补充后重试。")


def _run_auth_fetch(cfg, args):
    """执行登录信息获取（自动发现/自动启动浏览器，或手动粘贴），返回 (auth, launched)。"""
    if getattr(args, "manual", False):
        a = auth.manual_auth(cfg, cookie=getattr(args, "cookie", None),
                             auth_value=getattr(args, "auth_value", None),
                             emp_no=getattr(args, "emp_no", None))
        return a, False
    try:
        ws_url = auth.discover_ws_url(cfg)
        launched = False
    except RuntimeError:
        if getattr(args, "no_launch", False):
            raise
        info = auth.launch_debug_browser(cfg)
        launched = True
        print(f"🚀 已自动启动浏览器（{os.path.basename(info['browser'])}，端口 {info['port']}），"
              "正在等待调试端口…")
        ws_url = auth.wait_for_debug_port(cfg, timeout=60)
    wait = getattr(args, "wait", None)
    if wait is None:
        wait = cfg.get("auth_wait_seconds", 120) if launched else 0
    a = auth.fetch_auth(cfg, ws_url=ws_url, wait_login=wait)
    return a, launched


def _ensure_auth(args, cfg):
    """平台操作前确保已有登录信息：缺失时先引导获取，再补齐其余配置。"""
    path = cfg.get("auth_file", "auth.json")
    if os.path.exists(path):
        return _auth(args)
    print("尚未获取研发云登录信息，需要先从浏览器获取登录态才能继续。")
    if not sys.stdin.isatty():
        raise SystemExit("请先完成登录信息获取，再重试本命令。")
    if not _confirm("现在自动获取登录信息（将打开或复用浏览器）？"):
        raise SystemExit("已取消。获取登录信息后可继续。")
    a, _ = _run_auth_fetch(cfg, args)
    auth.save_auth(a, path)
    print(f"✅ 登录信息已获取并保存到 {path}")
    return _auth(args)


def _collect_missing_after_auth(cfg):
    """登录信息获取成功后，把仍缺失的平台配置以自然语言向用户补齐。"""
    cfg = _merge_auth_into_cfg(cfg)
    missing = _missing_fields(cfg, PLATFORM_FIELDS)
    if not missing:
        print("✅ 登录信息已提取，平台配置齐全，无需补充。")
        return
    if sys.stdin.isatty():
        print("\n登录信息已获取。还缺少以下平台信息，请补充（回车可跳过，稍后再补）：")
        _ask_fields(cfg, missing)
        still = _missing_fields(cfg, PLATFORM_FIELDS)
        if still:
            print("⚠ 仍缺少：" + "、".join(f"{l}（{k}）" for k, l in still) + "。")
            return
        if _confirm("是否将以上信息保存为全局配置，避免下次重复输入？", default=True):
            _save_runtime_config(cfg)
    else:
        print("⚠ 登录信息已获取。还需补充以下信息才能使用完整功能：")
        for k, l in missing:
            print(f"  - {l}（{k}）")
        print("  请补充后重试；补充前提交统计（stats）等离线命令不受影响。")


def _auth(args):
    cfg = _cfg(args)
    path = cfg.get("auth_file", "auth.json")
    try:
        a = auth.load_auth(path)
    except FileNotFoundError as e:
        raise SystemExit(f"❌ {e}") from None
    # 请求头跟随配置中已提供的平台参数，避免使用保存时的占位符
    headers = a.setdefault("headers", {})
    for hk, key in (("x-api-key", "api_key"), ("x-tenant-id", "tenant_id"),
                    ("x-project-id", "project_id"), ("x-emp-no", "assignee_emp_no")):
        v = cfg.get(key, "")
        if v and not _is_placeholder(v):
            headers[hk] = v
    max_hours = cfg.get("auth_max_age_hours", 12)
    if auth.auth_is_stale(a, max_hours):
        print(f"⚠ 登录信息提取于 {a.get('fetched_at')}，可能已过期（>{max_hours}h）。"
              "如果接口返回 403，请重新获取登录信息。")
    return a


# ---------- 首次配置向导 ----------
PLACEHOLDERS = ("YOUR_WORKSPACE", "YOUR_PROJECT_ID", "YOUR_TEAM_ID", "YOUR_TENANT_ID",
                "YOUR_API_KEY", "YOUR_EMP_NO", "YOUR_NAME", "YOUR_TEAM_NAME", "YOUR_GIT_AUTHOR")

SETUP_FIELDS = [
    ("workspace", "工作区（workspace）", False),
    ("project_id", "项目 ID（x-project-id）", False),
    ("team_id", "团队 ID（teamId）", False),
    ("tenant_id", "租户 ID（x-tenant-id）", False),
    ("api_key", "API Key（x-api-key）", True),
    ("assignee_emp_no", "员工号（assignee_emp_no）", False),
    ("assignee_name", "姓名（assignee_name）", False),
    ("team_name", "团队名称（team_name）", False),
    ("git_author", "Git 作者（git_author）", False),
]


def _mask(value):
    if not value or str(value).startswith("YOUR_"):
        return "未设置"
    return "***" + str(value)[-4:]


def _resolve_setup_values(args, current):
    """交互或 flags 收集配置值，返回更新后的配置 dict。"""
    cfg = dict(current)
    provided = {
        "workspace": args.workspace, "project_id": args.project_id,
        "team_id": args.team_id, "tenant_id": args.tenant_id,
        "api_key": args.api_key, "assignee_emp_no": args.assignee_emp_no,
        "assignee_name": args.assignee_name, "team_name": args.team_name,
        "git_author": args.git_author,
        "work_item_type": args.work_item_type, "task_type": args.task_type,
        "chrome_debug_port": args.chrome_debug_port,
    }
    for k, v in provided.items():
        if v is not None:
            cfg[k] = v
    if args.repos:
        cfg["repos"] = [r.strip() for r in args.repos.split(",") if r.strip()]

    if args.no_input:
        return cfg

    print("首次配置向导（回车使用当前值）：")
    for key, label, secret in SETUP_FIELDS:
        cur = cfg.get(key, "")
        if secret:
            hint = "未设置" if not str(cur).startswith("YOUR_") else _mask(cur)
            raw = getpass.getpass(f"  {label} [{hint}]: ").strip()
        else:
            raw = input(f"  {label} [{cur}]: ").strip()
        if raw:
            cfg[key] = raw
    return cfg


def cmd_setup_config(args):
    """首次配置向导：把用户提供的平台参数写入全局配置文件（多平台路径）。"""
    if not sys.stdin.isatty() and not args.no_input:
        raise SystemExit("非交互环境请使用 --no-input 通过 flags 提供配置值，并加 --yes 确认写入。")
    cfg = config.load_config()
    data = _resolve_setup_values(args, cfg)
    # 可移植性：auth_file 不写入全局配置（每次按本机 user_config_dir 计算）
    data.pop("auth_file", None)
    # chrome_profile_dir 还原为 ~ 形式，避免固化本机绝对路径
    home = os.path.expanduser("~")
    cd = data.get("chrome_profile_dir", "")
    if isinstance(cd, str) and cd.startswith(home + os.sep):
        data["chrome_profile_dir"] = "~" + cd[len(home):]
    path = config.global_config_path()
    print("将写入全局配置：", path)
    print("  workspace :", data.get("workspace"))
    print("  team_id   :", data.get("team_id"))
    print("  api_key   :", _mask(data.get("api_key")))
    print("  assignee  :", data.get("assignee_name"), data.get("assignee_emp_no"))
    print("  git_author:", data.get("git_author"))
    if not (args.yes or args.no_input):
        ok = input("确认写入？[y/N] ").strip().lower()
        if ok not in ("y", "yes"):
            print("已取消")
            return
    config.write_global_config(data, path)
    print(f"✅ 已写入全局配置 {path}")
    print(f"   鉴权文件将保存到 {config.user_config_dir()}/auth.json")
    print("   后续命令无需 --config 自动加载；Windows 路径为 %APPDATA%\\rdc-work-items.yaml")


# ---------- 命令实现 ----------
def cmd_doctor(args):
    cfg = _cfg(args)
    ok, lines = doctor.run(cfg, cfg.get("auth_file", "auth.json"))
    print("\n".join(lines))
    raise SystemExit(0 if ok else 1)


def cmd_auth(args):
    """获取登录信息：从浏览器提取登录态，随后把仍缺失的配置向用户补齐。"""
    cfg = _cfg(args)
    a, launched = _run_auth_fetch(cfg, args)
    path = auth.save_auth(a, cfg.get("auth_file", "auth.json"))
    print(f"✅ 登录信息已保存到 {path}")
    print(f"   员工号: {a['emp_no']} | 项目: {a['project_id']} | 团队: {a['team_id']} | 工作区: {a['workspace']}")
    print(f"   提取时间: {a['fetched_at']} | 来源: {a.get('source', 'cdp')}")
    _collect_missing_after_auth(cfg)


def cmd_stats(args):
    cfg = _cfg(args)
    since = args.since or cfg.get("git_since") or stats.default_range()[0]
    until = args.until or cfg.get("git_until") or stats.default_range()[1]
    if not (args.since and args.until):
        print(f"ℹ 未指定完整时间区间，使用默认区间 {since} ~ {until}")
    repos = ([r.strip() for r in args.repos.split(",") if r.strip()]
             if args.repos else list(cfg.get("repos") or []))
    if not repos:
        if sys.stdin.isatty():
            print("尚未配置待统计的 git 仓库。")
            raw = input("请提供仓库路径（多个用英文逗号分隔）: ").strip()
            repos = [r.strip() for r in raw.split(",") if r.strip()] if raw else []
        if not repos:
            raise SystemExit("尚未提供待统计的 git 仓库路径。请提供仓库路径后重试。")
    cfg_author = cfg.get("git_author")
    author = args.author or (None if _is_placeholder(cfg_author) else cfg_author)
    if not author and not args.author and sys.stdin.isatty():
        raw = input("Git 作者（仅统计该作者的提交，回车统计全部）: ").strip()
        author = raw or None
    if not author and not args.author:
        print("ℹ 未配置 Git 作者，将统计全部作者的提交（如需只统计本人，请补充 Git 作者）。")
    r = stats.extract(cfg, since, until, author=author, repos=repos,
                      include_noise=args.include_noise)
    if args.out:
        stats.dump(r, args.out)
        print(f"✅ 提交数据已保存到 {args.out}")
    shown_author = r["author"] or "全部作者"
    print(f"业务提交总数: {r['total_business_commits']}（统计范围: {shown_author}，{r['since']} ~ {r['until']}）")
    for repo in r["repos"]:
        print(f"  {repo['repo']}: {repo['count']}")


def cmd_build_excel(args):
    cfg = _merge_auth_into_cfg(_cfg(args))
    missing = _missing_fields(cfg, EXCEL_INFO_FIELDS)
    if missing:
        if sys.stdin.isatty():
            print("\n生成 Excel 前还缺少以下信息（会体现在「指派给/创建人/团队」列）：")
            _ask_fields(cfg, missing)
            if _confirm("是否将本次补充的信息保存为全局配置？", default=True):
                _save_runtime_config(cfg)
        else:
            print("ℹ 缺少以下信息，Excel 中「指派给/创建人/团队」等列将留空："
                  + "、".join(f"{l}（{k}）" for k, l in missing))
    items = excelgen.load_items(args.input)
    r = excelgen.build(cfg, items, args.out, status=args.status,
                       updated_at=args.updated_at, created_at=args.created_at)
    print(f"✅ 已生成工作量 Excel {r['out']}：{r['items']} 条，状态={r['status']}")


def _summarize_bo(bo, max_len=100):
    """把平台返回体压成可读摘要（长对象截断），避免整段 JSON 刷屏。"""
    lines = []
    for k, v in bo.items():
        if isinstance(v, (dict, list)):
            s = json.dumps(v, ensure_ascii=False)
            if len(s) > max_len:
                s = s[:max_len] + "…"
        else:
            s = str(v)
        lines.append(f"  {k}: {s}")
    return "\n".join(lines)


def cmd_validate(args):
    cfg = _cfg(args)
    _ensure_auth(args, cfg)
    cfg = _ensure_config(args, cfg, PLATFORM_FIELDS, "校验导入文件")
    bo = api.validate(cfg, _auth(args), args.file)
    if args.verbose:
        print("校验结果：", json.dumps(bo, ensure_ascii=False, indent=2))
    else:
        print("校验结果：")
        print(_summarize_bo(bo))


def cmd_prepare(args):
    cfg = _cfg(args)
    status = args.status or cfg.get("initial_status", "新建")
    r = prepare.prepare(args.src, args.out, status=status, keep_ids=args.keep_ids,
                        keep_updated_time=args.keep_updated_time)
    for w in r.get("warnings", []):
        print("⚠", w)
    print(f"✅ 已生成导入文件 {r['out']}：{r['items']} 条，状态={r['status']}")
    print(f"   列：{r['columns']}")


def cmd_update_status(args):
    """通过 updateWorkItems/edit 接口流转状态（不再走 Excel 导入）。"""
    cfg = _cfg(args)
    if args.ids:
        ids = [i.strip() for i in args.ids.split(",") if i.strip()]
    else:
        if not args.file:
            raise SystemExit("缺少工作项来源：需提供 file（读取编号列）或 --ids")
        ids = prepare.collect_ids(args.file)
    if not ids:
        raise SystemExit("未获取到任何工作项编号")
    flow = cfg.get("status_flow", ["新建", "处理中", "已完成", "已关闭"])
    shown = ", ".join(ids[:10]) + ("…" if len(ids) > 10 else "")
    print(f"目标状态：{args.status}（状态流：{' → '.join(flow)}）")
    print(f"工作项编号（{len(ids)} 条）：{shown}")
    if args.dry_run:
        print("⚠ 预览（dry-run）模式：已列出将流转的工作项，本次未调用接口、未做任何修改。")
        return
    if args.status not in flow:
        raise SystemExit(f"目标状态「{args.status}」不在状态流（{' → '.join(flow)}）中，无法流转")
    if not args.yes:
        if not _confirm(f"确认将 {len(ids)} 条工作项状态流转为「{args.status}」？"):
            print("已取消。可先加 --dry-run 预览，或加 --yes 跳过确认。")
            return
    _ensure_auth(args, cfg)
    cfg = _ensure_config(args, cfg, PLATFORM_FIELDS, "流转工作项状态")
    bo = api.update_work_items_state(cfg, _auth(args), ids, args.status)
    succeeded = bo.get("succeededItems", [])
    failed = bo.get("failedItems", [])
    print(f"✅ 已更新 {len(succeeded)}/{len(ids)} 条状态为「{args.status}」")
    if failed:
        print("⚠ 失败项：", json.dumps(failed, ensure_ascii=False)[:1000])


def cmd_summary(args):
    items = prepare.summarize(args.file)
    print(f"文件 {args.file} 共 {len(items)} 条：")
    for it in items:
        print(f"  {it['编号'] or '(新)'} | {it['状态']} | {it['标题']}")


def _save_error_report(url, auth_data, out_dir, cfg):
    """下载平台错误报告并保存为本地 xlsx，返回保存路径。"""
    rpt = api.download(url, auth_data)
    path = os.path.join(out_dir, "错误报告.xlsx")
    with open(path, "wb") as f:
        f.write(rpt["content"])
    return path, rpt["text"]


def cmd_import(args):
    cfg = _cfg(args)
    _ensure_auth(args, cfg)
    cfg = _ensure_config(args, cfg, PLATFORM_FIELDS, "导入工作项")
    auth_data = _auth(args)
    # 导入前先只读校验，打印预计新增/更新
    bo = api.validate(cfg, auth_data, args.file)
    msg = bo.get("successMsg") or bo.get("errMsg") or "校验通过"
    print(f"校验：{msg}")
    if args.verbose:
        print(json.dumps(bo, ensure_ascii=False, indent=2))
    else:
        print(_summarize_bo(bo))
    if not args.yes:
        if not _confirm("确认导入到研发云（将创建/更新工作项）？"):
            print("已取消")
            return
    task = api.import_items(cfg, auth_data, args.file, team_id=args.team_id)
    ids = api.import_ids(task)
    ok_n = task.get("succeededItemsSize", len(ids))
    failed_n = task.get("failedItemsSize", 0)
    print(f"✅ 导入完成：成功 {ok_n} 条，失败 {failed_n} 条")
    if ids:
        shown = ", ".join(ids[:5]) + ("…" if len(ids) > 5 else "")
        print(f"   工作项编号：{shown}")
    if failed_n > 0:
        url = task.get("fileUrl", "")
        if url:
            out_dir = os.path.dirname(os.path.abspath(args.file)) or "."
            report, text = _save_error_report(url, auth_data, out_dir, cfg)
            print(f"⚠ 失败 {failed_n} 条，错误报告已保存：{report}")
            print("   报告前 500 字：", text[:500])
        else:
            print(f"⚠ 失败 {failed_n} 条，但平台未返回错误报告 fileUrl")
    if args.verbose:
        print("完整响应：", json.dumps(task, ensure_ascii=False, indent=2))


def cmd_export(args):
    cfg = _cfg(args)
    _ensure_auth(args, cfg)
    cfg = _ensure_config(args, cfg, PLATFORM_FIELDS, "导出工作项")
    r = api.export_excel(cfg, _auth(args), args.out, since=args.since, until=args.until,
                         assignee=args.assignee, state=args.state, page_size=args.page_size)
    print(f"✅ 已导出 {r['saved']}（{r['bytes']} 字节，共 {r['task'].get('totalSize', '?')} 条）")


def _save_flow_ids(out_dir, ids, flow):
    path = os.path.join(out_dir, "ids.json")
    data = {"ids": ids, "status_flow": flow,
            "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def _load_flow_ids(out_dir):
    path = os.path.join(out_dir, "ids.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("ids", [])


def cmd_flow(args):
    """全流程多模式（默认预览，确认后执行）：
    - full   ：prepare → validate → import(创建) → updateWorkItems 接口逐级流转
    - import ：只创建，编号保存到 out-dir/ids.json（供 status 模式续跑）
    - status ：只流转状态（读取 out-dir/ids.json 或 --ids），断点续跑/幂等
    """
    cfg = _cfg(args)
    os.makedirs(args.out_dir, exist_ok=True)
    flow = cfg.get("status_flow", ["新建", "处理中", "已完成", "已关闭"])
    mode = args.mode
    ids = [i.strip() for i in (args.ids or "").split(",") if i.strip()] if args.ids else []
    if ids and mode == "full":
        mode = "status"  # 已提供编号则跳过创建，只做状态流转

    if mode in ("full", "import"):
        if not args.src:
            raise SystemExit(f"flow --mode {mode} 需要 --src（工作量 Excel）")
        count = len(prepare.summarize(args.src))
        print(f"工作流状态：{' → '.join(flow)}（共 {count} 条）")
        initial = flow[0]
        imp0 = os.path.join(args.out_dir, f"导入-{initial}.xlsx")
        prep = prepare.prepare(args.src, imp0, status=initial)
        for w in prep.get("warnings", []):
            print("⚠", w)
        _ensure_auth(args, cfg)
        cfg = _ensure_config(args, cfg, PLATFORM_FIELDS, "创建并流转工作项")
        bo = api.validate(cfg, _auth(args), imp0)
        print(f"[1/2] 校验创建文件：{bo.get('successMsg') or bo.get('errMsg') or '通过'}")
        if not args.yes:
            print("⚠ 预览模式：已校验创建文件，尚未创建任何工作项。")
            if not _confirm("确认执行创建？"):
                print("已取消，未创建任何工作项。")
                return
        task = api.import_items(cfg, _auth(args), imp0)
        if task.get("failedItemsSize", 0) > 0:
            print("❌ 创建导入失败：", json.dumps(task, ensure_ascii=False)[:800])
            url = task.get("fileUrl", "")
            if url:
                report, _ = _save_error_report(url, _auth(args), args.out_dir, cfg)
                print(f"   错误报告已保存：{report}")
            return
        ids = api.import_ids(task)
        print(f"✅ 创建成功：{task.get('succeededItemsSize')} 条")
        if not ids:
            print("⚠ 未能从导入响应提取工作项编号，跳过状态流转")
            return
        ids_path = _save_flow_ids(args.out_dir, ids, flow)
        print(f"   工作项编号：{', '.join(ids)}")
        print(f"   已保存到 {ids_path}")
        if mode == "import":
            if not _confirm("已创建工作项（状态为「新建」）。是否继续把状态流转为"
                            f"「{' → '.join(flow[1:])}」？", default=True):
                print("已保存工作项编号，需要时再继续流转即可。")
                return
            args.yes = True  # 用户已确认继续

    # mode == "status"
    if not ids:
        ids = _load_flow_ids(args.out_dir)
    if not ids:
        raise SystemExit("未获取到工作项编号。请先创建并导入工作项，或提供已有编号。")
    print(f"状态流转：{' → '.join(flow)}（共 {len(ids)} 条）")
    shown = ", ".join(ids[:10]) + ("…" if len(ids) > 10 else "")
    print(f"   工作项编号：{shown}")
    if not args.yes:
        print("⚠ 预览模式：已列出将流转的工作项，本次未调用接口、未做任何修改。")
        if not _confirm("确认执行状态流转？"):
            print("已取消。")
            return
    _ensure_auth(args, cfg)
    cfg = _ensure_config(args, cfg, PLATFORM_FIELDS, "流转工作项状态")
    for st in flow[1:]:
        bo = api.update_work_items_state(cfg, _auth(args), ids, st)
        ok = len(bo.get("succeededItems", []))
        failed = bo.get("failedItems", [])
        if failed:
            print(f"❌ 状态 {st} 更新失败：{json.dumps(failed, ensure_ascii=False)[:500]}")
            break
        print(f"✅ 状态 {st} 更新成功：{ok}/{len(ids)} 条")
    print("🎉 流程完成。工作项编号：", ", ".join(ids))


# ---------- 参数 ----------
def main():
    p = argparse.ArgumentParser(prog="rdc", description="研发云工作项自动化工具（配置驱动，纯标准库）")
    p.add_argument("--config", default=None, help="配置文件路径（yaml/json），默认自动查找 rdc-config.yaml 或全局配置")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(subp, name, **kw):
        return subp.add_parser(name, **kw)

    pc = add(sub, "setup-config", help="首次配置向导：写入全局配置（多平台）")
    pc.add_argument("--workspace", default=None)
    pc.add_argument("--project-id", default=None)
    pc.add_argument("--team-id", default=None)
    pc.add_argument("--tenant-id", default=None)
    pc.add_argument("--api-key", default=None)
    pc.add_argument("--assignee-emp-no", default=None)
    pc.add_argument("--assignee-name", default=None)
    pc.add_argument("--team-name", default=None)
    pc.add_argument("--work-item-type", default=None)
    pc.add_argument("--task-type", default=None)
    pc.add_argument("--git-author", default=None)
    pc.add_argument("--repos", default=None, help="逗号分隔的 git 仓库路径")
    pc.add_argument("--chrome-debug-port", type=int, default=None)
    pc.add_argument("--no-input", action="store_true", help="非交互：仅使用 flags 提供的值")
    pc.add_argument("--yes", action="store_true", help="跳过写入确认")
    pc.set_defaults(func=cmd_setup_config)

    pd = add(sub, "doctor", help="环境自检：配置/鉴权/调试端口/git 仓库（只读）")
    pd.set_defaults(func=cmd_doctor)

    pa = add(sub, "auth", help="提取鉴权数据（自动发现/自动启动浏览器，或 --manual 手动粘贴）")
    pa.add_argument("--manual", action="store_true", help="手动模式：粘贴 Cookie 头")
    pa.add_argument("--cookie", default=None, help="手动模式：Cookie 头（F12 复制）")
    pa.add_argument("--auth-value", default=None, help="手动模式：x-auth-value")
    pa.add_argument("--emp-no", default=None, help="手动模式：员工号")
    pa.add_argument("--no-launch", action="store_true", help="不自动启动浏览器（未发现调试端口时报错）")
    pa.add_argument("--wait", type=int, default=None,
                    help="等待登录秒数（自动启动后默认 auth_wait_seconds；复用已有浏览器默认不等待）")
    pa.set_defaults(func=cmd_auth)

    ps = add(sub, "stats", help="提取 git 提交（供 AI 分组为工作项）")
    ps.add_argument("--since", default=None, help="开始日期，缺省用配置 git_since 或当月 1 号")
    ps.add_argument("--until", default=None, help="结束日期，缺省用配置 git_until 或今天")
    ps.add_argument("--author", default=None)
    ps.add_argument("--repos", default=None, help="逗号分隔的仓库列表，缺省用配置")
    ps.add_argument("--include-noise", action="store_true")
    ps.add_argument("-o", "--out", default=None)
    ps.set_defaults(func=cmd_stats)

    pb = add(sub, "build-excel", help="从工作项 JSON 生成工作量 Excel")
    pb.add_argument("-i", "--input", required=True)
    pb.add_argument("-o", "--out", required=True)
    pb.add_argument("--status", default=None)
    pb.add_argument("--updated-at", default="")
    pb.add_argument("--created-at", default="")
    pb.set_defaults(func=cmd_build_excel)

    pv = add(sub, "validate", help="校验导入文件（只读）")
    pv.add_argument("file")
    pv.add_argument("--verbose", action="store_true", help="打印完整平台返回")
    pv.set_defaults(func=cmd_validate)

    pp = add(sub, "prepare", help="生成导入文件（改状态/清编号）")
    pp.add_argument("src")
    pp.add_argument("-o", "--out", required=True)
    pp.add_argument("--status", default=None)
    pp.add_argument("--keep-ids", action="store_true")
    pp.add_argument("--keep-updated-time", action="store_true")
    pp.set_defaults(func=cmd_prepare)

    pss = add(sub, "update-status", help="通过接口批量流转工作项状态")
    pss.add_argument("file", nargs="?", default=None, help="xlsx 文件（读取编号列）")
    pss.add_argument("--status", required=True, help="目标状态（须按 status_flow 逐级流转）")
    pss.add_argument("--ids", default=None, help="逗号分隔的工作项编号，与 file 二选一")
    pss.add_argument("--dry-run", action="store_true", help="只打印将执行的操作，不调用接口")
    pss.add_argument("--yes", action="store_true", help="跳过状态流转确认（非交互环境需加 --yes）")
    pss.set_defaults(func=cmd_update_status)

    psm = add(sub, "summary", help="查看文件内工作项")
    psm.add_argument("file")
    psm.set_defaults(func=cmd_summary)

    pi = add(sub, "import", help="导入工作项（默认需确认，--yes 跳过）")
    pi.add_argument("file")
    pi.add_argument("--team-id", default=None)
    pi.add_argument("--yes", action="store_true", help="跳过导入确认")
    pi.add_argument("--verbose", action="store_true", help="打印完整平台返回")
    pi.set_defaults(func=cmd_import)

    pe = add(sub, "export", help="导出工作项 Excel")
    pe.add_argument("-o", "--out", required=True)
    pe.add_argument("--since")
    pe.add_argument("--until")
    pe.add_argument("--assignee", default=None)
    pe.add_argument("--state", default="@all")
    pe.add_argument("--page-size", type=int, default=200)
    pe.set_defaults(func=cmd_export)

    pf = add(sub, "flow", help="全流程多模式（默认 dry-run，加 --yes 执行）")
    pf.add_argument("--src", default=None, help="工作量 Excel（mode=full/import 必填）")
    pf.add_argument("--out-dir", default="flow")
    pf.add_argument("--mode", choices=["full", "import", "status"], default="full",
                    help="full=导入+流转；import=只创建；status=只流转（续跑）")
    pf.add_argument("--ids", default=None, help="工作项编号（status 模式指定，缺省读 out-dir/ids.json）")
    pf.add_argument("--since")
    pf.add_argument("--until")
    pf.add_argument("--assignee", default=None)
    pf.add_argument("--yes", action="store_true", help="确认执行导入与状态流转（否则仅校验/预览）")
    pf.set_defaults(func=cmd_flow)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
