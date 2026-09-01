# -*- coding: utf-8 -*-
"""研发云工作项自动化 CLI（配置驱动，所有环境变量可在 config.yaml 自定义）

纯标准库运行（无需 pip 安装依赖）。状态流转走 updateWorkItems/edit 接口。

用法：
  python -m rdc.cli --config rdc-config.yaml auth
  python -m rdc.cli stats --since 2026-08-01 --until 2026-08-31 -o commits.json
  python -m rdc.cli build-excel -i work_items.json -o 营销域8月-示例.xlsx
  python -m rdc.cli prepare 营销域8月-示例.xlsx -o 导入-新建.xlsx --status 新建
  python -m rdc.cli validate 导入-新建.xlsx
  python -m rdc.cli import 导入-新建.xlsx
  python -m rdc.cli export -o 导出.xlsx --since 2026-08-01 --until 2026-08-31
  python -m rdc.cli update-status 导出.xlsx --status 处理中        # 接口流转
  python -m rdc.cli update-status --ids P22CQQYYF0016-6864 --status 已完成
  python -m rdc.cli flow --src 营销域8月-示例.xlsx --out-dir flow  # 全流程（默认 dry-run）
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rdc import api, auth, config, excelgen, prepare, stats


def _cfg(args):
    return config.load_config(getattr(args, "config", None))


def _auth_path(args):
    return _cfg(args).get("auth_file", "auth.json")


def _auth(args):
    return auth.load_auth(_auth_path(args))


# ---------- 命令实现 ----------
def cmd_auth(args):
    cfg = _cfg(args)
    a = auth.fetch_auth(cfg)
    path = auth.save_auth(a, cfg.get("auth_file", "auth.json"))
    print(f"✅ 鉴权已保存到 {path}")
    print(f"   员工号: {a['emp_no']} | 项目: {a['project_id']} | 团队: {a['team_id']} | 工作区: {a['workspace']}")
    print(f"   提取时间: {a['fetched_at']}")


def cmd_stats(args):
    cfg = _cfg(args)
    r = stats.extract(cfg, args.since, args.until, author=args.author,
                      repos=args.repos.split(",") if args.repos else None,
                      include_noise=args.include_noise)
    if args.out:
        stats.dump(r, args.out)
        print(f"✅ 提交数据已保存到 {args.out}")
    print(f"业务提交总数: {r['total_business_commits']}（作者 {r['author']}，{r['since']} ~ {r['until']}）")
    for repo in r["repos"]:
        print(f"  {repo['repo']}: {repo['count']}")


def cmd_build_excel(args):
    cfg = _cfg(args)
    items = excelgen.load_items(args.input)
    r = excelgen.build(cfg, items, args.out, status=args.status,
                       updated_at=args.updated_at, created_at=args.created_at)
    print(f"✅ 已生成工作量 Excel {r['out']}：{r['items']} 条，状态={r['status']}")


def cmd_validate(args):
    cfg = _cfg(args)
    bo = api.validate(cfg, _auth(args), args.file)
    print("校验结果：", json.dumps(bo, ensure_ascii=False, indent=2))


def cmd_prepare(args):
    cfg = _cfg(args)
    status = args.status or cfg.get("initial_status", "新建")
    r = prepare.prepare(args.src, args.out, status=status, keep_ids=args.keep_ids,
                        keep_updated_time=args.keep_updated_time)
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


def cmd_import(args):
    cfg = _cfg(args)
    task = api.import_items(cfg, _auth(args), args.file, team_id=args.team_id)
    print("导入结果：", json.dumps(task, ensure_ascii=False, indent=2))
    if task.get("failedItemsSize", 0) > 0:
        url = task.get("fileUrl", "")
        if url:
            rpt = api.download(url, _auth(args))
            print("⚠ 失败原因：", rpt["text"][:1000])


def cmd_export(args):
    cfg = _cfg(args)
    r = api.export_excel(cfg, _auth(args), args.out, since=args.since, until=args.until,
                         assignee=args.assignee, state=args.state, page_size=args.page_size)
    print(f"✅ 已导出 {r['saved']}（{r['bytes']} 字节，共 {r['task'].get('totalSize', '?')} 条）")


def cmd_flow(args):
    """全流程：prepare → validate → import(创建) → updateWorkItems 接口逐级流转。
    默认 dry-run（只校验不导入）；加 --yes 才真正执行。"""
    cfg = _cfg(args)
    os.makedirs(args.out_dir, exist_ok=True)
    flow = cfg.get("status_flow", ["新建", "处理中", "已完成", "已关闭"])
    initial = flow[0]
    count = len(prepare.summarize(args.src))
    print(f"工作流状态：{' → '.join(flow)}（共 {count} 条）")

    # 1) 初始导入文件
    imp0 = os.path.join(args.out_dir, f"导入-{initial}.xlsx")
    prepare.prepare(args.src, imp0, status=initial)
    bo = api.validate(cfg, _auth(args), imp0)
    print(f"[1/2] 校验创建文件：{bo.get('successMsg') or bo.get('errMsg')}")
    if not args.yes:
        print("⚠ dry-run 模式：未执行导入。确认无误后加 --yes 执行。")
        return
    task = api.import_items(cfg, _auth(args), imp0)
    if task.get("failedItemsSize", 0) > 0:
        print("❌ 创建导入失败：", json.dumps(task, ensure_ascii=False))
        return
    print(f"✅ 创建成功：{task.get('succeededItemsSize')} 条")
    ids = api.import_ids(task)
    if not ids:
        print("⚠ 未能从导入响应提取工作项编号，跳过状态流转")
        return
    print(f"   工作项编号：{', '.join(ids)}")

    # 2) 接口逐级流转（不再导出/导入 Excel）
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
    p.add_argument("--config", default=None, help="配置文件路径（yaml/json），默认自动查找 rdc-config.yaml")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(subp, name, **kw):
        return subp.add_parser(name, **kw)

    pa = add(sub, "auth", help="通过 CDP 提取鉴权数据")
    pa.set_defaults(func=cmd_auth)

    ps = add(sub, "stats", help="提取 git 提交（供 AI 分组为工作项）")
    ps.add_argument("--since", required=True)
    ps.add_argument("--until", required=True)
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
    pss.set_defaults(func=cmd_update_status)

    psm = add(sub, "summary", help="查看文件内工作项")
    psm.add_argument("file")
    psm.set_defaults(func=cmd_summary)

    pi = add(sub, "import", help="导入工作项")
    pi.add_argument("file")
    pi.add_argument("--team-id", default=None)
    pi.set_defaults(func=cmd_import)

    pe = add(sub, "export", help="导出工作项 Excel")
    pe.add_argument("-o", "--out", required=True)
    pe.add_argument("--since")
    pe.add_argument("--until")
    pe.add_argument("--assignee", default=None)
    pe.add_argument("--state", default="@all")
    pe.add_argument("--page-size", type=int, default=200)
    pe.set_defaults(func=cmd_export)

    pf = add(sub, "flow", help="全流程（默认 dry-run，加 --yes 执行导入与状态流转）")
    pf.add_argument("--src", required=True, help="工作量 Excel（导出结果格式）")
    pf.add_argument("--out-dir", default="flow")
    pf.add_argument("--since")
    pf.add_argument("--until")
    pf.add_argument("--assignee", default=None)
    pf.add_argument("--yes", action="store_true", help="确认执行导入与状态流转（否则仅校验）")
    pf.set_defaults(func=cmd_flow)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
