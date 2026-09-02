# -*- coding: utf-8 -*-
"""CLI 离线端到端测试（子进程运行，纯标准库）：python3 tests/test_cli.py"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")


def _run(*args, cwd):
    return subprocess.run([sys.executable, "rdc_workflow", *args],
                          cwd=cwd, capture_output=True, text=True, timeout=120)


def test_full_offline_flow():
    tmp = tempfile.mkdtemp(prefix="rdc-cli-")
    shutil.copytree(SCRIPTS, os.path.join(tmp, "scripts"))
    wi = os.path.join(tmp, "work_items.json")
    with open(wi, "w", encoding="utf-8") as f:
        json.dump({"work_items": [
            {"title": "前端开发-资金归集-登录", "hours": 8,
             "start": "2026-08-01", "end": "2026-08-05", "description": "完成登录模块"},
        ]}, f, ensure_ascii=False)

    # build-excel
    xlsx_path = os.path.join(tmp, "8月-示例.xlsx")
    r = _run("build-excel", "-i", wi, "-o", xlsx_path, cwd=os.path.join(tmp, "scripts"))
    assert r.returncode == 0, r.stderr
    assert os.path.exists(xlsx_path)

    # summary
    r = _run("summary", xlsx_path, cwd=os.path.join(tmp, "scripts"))
    assert r.returncode == 0, r.stderr
    assert "前端开发-资金归集-登录" in r.stdout

    # prepare
    imp = os.path.join(tmp, "导入-新建.xlsx")
    r = _run("prepare", xlsx_path, "-o", imp, "--status", "新建", cwd=os.path.join(tmp, "scripts"))
    assert r.returncode == 0, r.stderr
    r = _run("summary", imp, cwd=os.path.join(tmp, "scripts"))
    assert "新建" in r.stdout

    # update-status 缺参报错（不联网）
    r = _run("update-status", "--status", "处理中", cwd=os.path.join(tmp, "scripts"))
    assert r.returncode != 0
    assert "缺少工作项来源" in r.stderr or "缺少工作项来源" in r.stdout


def test_no_third_party_imports():
    """rdc 包内不得 import 任何第三方库（websocket/requests/yaml/openpyxl）。"""
    pkg = os.path.join(SCRIPTS, "rdc")
    forbidden = ("websocket", "requests", "pyyaml", "openpyxl")
    import_pat = re.compile(
        r"^\s*(?:import|from)\s+\S*(" + "|".join(forbidden) + r")", re.M)
    for fn in os.listdir(pkg):
        if not fn.endswith(".py"):
            continue
        text = open(os.path.join(pkg, fn), encoding="utf-8").read()
        m = import_pat.search(text)
        assert m is None, f"{fn} 仍引用第三方依赖: {m.group(1)}"
    print("  ✅ 无第三方依赖引用")

def test_version_flag():
    r = _run("--version", cwd=SCRIPTS)
    assert r.returncode == 0
    assert "2.3.0" in r.stdout


def test_update_status_dry_run():
    r = _run("update-status", "--ids", "P22TEST0000001-6864,P22TEST0000001-6865",
             "--status", "处理中", "--dry-run", cwd=SCRIPTS)
    assert r.returncode == 0
    assert "dry-run" in r.stdout
    assert "P22TEST0000001-6864" in r.stdout


def test_flow_status_mode_requires_ids():
    tmp = tempfile.mkdtemp(prefix="rdc-flow-")
    r = _run("flow", "--mode", "status", "--out-dir", tmp, cwd=SCRIPTS)
    assert r.returncode != 0
    assert "未获取到工作项编号" in r.stderr or "未获取到工作项编号" in r.stdout


def test_flow_ids_helpers():
    sys.path.insert(0, SCRIPTS)
    from rdc import cli
    tmp = tempfile.mkdtemp(prefix="rdc-ids-")
    flow = ["新建", "处理中", "已完成", "已关闭"]
    path = cli._save_flow_ids(tmp, ["A-1", "A-2"], flow)
    assert os.path.exists(path)
    assert cli._load_flow_ids(tmp) == ["A-1", "A-2"]
    assert cli._load_flow_ids(os.path.join(tmp, "none")) == []


def test_summarize_bo_truncates():
    sys.path.insert(0, SCRIPTS)
    from rdc import cli
    out = cli._summarize_bo({"successMsg": "预计新增 1 条", "huge": list(range(500))})
    assert "预计新增 1 条" in out
    assert "…" in out


def test_import_confirm_flow():
    """import 默认需确认：拒绝时只校验不导入；--yes 跳过确认直接导入。"""
    sys.path.insert(0, SCRIPTS)
    import io
    import contextlib
    from rdc import api, cli

    tmp = tempfile.mkdtemp(prefix="rdc-import-")
    auth_path = os.path.join(tmp, "auth.json")
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump({"headers": {}, "fetched_at": "2026-09-02 10:00:00"}, f)
    cfg_path = os.path.join(tmp, "rdc-config.yaml")
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(
            f"auth_file: {auth_path}\n"
            "workspace: P22TEST0000001\nproject_id: P\nteam_id: T\n"
            "tenant_id: 20001\napi_key: K\nassignee_emp_no: E\n"
            "assignee_name: N\nteam_name: M\n")

    class Args:
        file = "导入-新建.xlsx"
        yes = False
        verbose = False
        team_id = None
        config = cfg_path

    orig_auth, orig_validate, orig_import, orig_confirm = (
        cli._auth, api.validate, api.import_items, cli._confirm)
    calls = {"validate": 0, "import": 0}

    def fake_validate(cfg, a, f):
        calls["validate"] += 1
        return {"successMsg": "预计新增 1 条"}

    def fake_import(cfg, a, f, team_id=None):
        calls["import"] += 1
        return {"succeededItemsSize": 1, "failedItemsSize": 0,
                "taskInfo": {"succeededItems": [{"data": {"1": "P22TEST0000001-6864"}}]}}

    cli._auth = lambda args: {"headers": {}}
    api.validate = fake_validate
    api.import_items = fake_import
    try:
        # 拒绝确认 → 不导入
        cli._confirm = lambda q, default=False: False
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.cmd_import(Args())
        assert calls["validate"] == 1 and calls["import"] == 0, "拒绝确认不应导入"
        assert "已取消" in buf.getvalue()
        # 确认 y → 导入
        cli._confirm = lambda q, default=False: True
        with contextlib.redirect_stdout(io.StringIO()):
            cli.cmd_import(Args())
        assert calls["import"] == 1
        # --yes → 不询问直接导入
        Args.yes = True
        with contextlib.redirect_stdout(io.StringIO()):
            cli.cmd_import(Args())
        assert calls["import"] == 2
    finally:
        cli._auth, api.validate, api.import_items, cli._confirm = (
            orig_auth, orig_validate, orig_import, orig_confirm)


def test_confirm_tty_and_non_tty():
    """_confirm：终端按 y 确认、回车用默认值；非终端不执行任何操作。"""
    sys.path.insert(0, SCRIPTS)
    import builtins
    from rdc import cli
    orig_stdin, orig_input = sys.stdin, builtins.input

    class FakeStdin:
        def isatty(self):
            return True

    try:
        sys.stdin = FakeStdin()
        builtins.input = lambda *a, **k: "y"
        assert cli._confirm("继续？") is True
        builtins.input = lambda *a, **k: ""
        assert cli._confirm("继续？", default=True) is True  # 回车用默认
        builtins.input = lambda *a, **k: "n"
        assert cli._confirm("继续？") is False
        sys.stdin = orig_stdin  # 非终端
        assert cli._confirm("继续？") is False  # 非交互不执行
    finally:
        sys.stdin, builtins.input = orig_stdin, orig_input


def test_placeholder_and_missing_fields():
    sys.path.insert(0, SCRIPTS)
    from rdc import cli
    assert cli._is_placeholder(None)
    assert cli._is_placeholder("")
    assert cli._is_placeholder("YOUR_WORKSPACE")
    assert not cli._is_placeholder("P22TEST")
    cfg = {"workspace": "YOUR_WORKSPACE", "team_id": "T1", "api_key": ""}
    fields = [("workspace", "工作区"), ("team_id", "团队 ID"), ("api_key", "API Key")]
    missing = cli._missing_fields(cfg, fields)
    assert [k for k, _ in missing] == ["workspace", "api_key"]


def test_merge_auth_into_cfg():
    """登录信息获取后回填配置中缺失的平台字段（先授权再补配置）。"""
    sys.path.insert(0, SCRIPTS)
    from rdc import cli
    tmp = tempfile.mkdtemp(prefix="rdc-merge-")
    auth_path = os.path.join(tmp, "auth.json")
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump({
            "emp_no": "E1001", "project_id": "PRJ1", "team_id": "TEAM1",
            "headers": {"x-tenant-id": "TENANT1", "x-api-key": "KEY1"},
        }, f)
    cfg = {"auth_file": auth_path, "workspace": "YOUR_WORKSPACE",
           "project_id": "", "team_id": "", "tenant_id": "", "api_key": ""}
    cli._merge_auth_into_cfg(cfg)
    assert cfg["assignee_emp_no"] == "E1001"
    assert cfg["project_id"] == "PRJ1"
    assert cfg["team_id"] == "TEAM1"
    assert cfg["tenant_id"] == "TENANT1"
    assert cfg["api_key"] == "KEY1"


def test_missing_config_natural_language():
    """平台命令缺配置时：非交互环境用自然语言列出缺失项，不抛命令。"""
    tmp = tempfile.mkdtemp(prefix="rdc-cfg-")
    auth_path = os.path.join(tmp, "auth.json")
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump({"headers": {}, "fetched_at": "2026-09-02 10:00:00"}, f)
    cfg_path = os.path.join(tmp, "rdc-config.yaml")
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(f"auth_file: {auth_path}\nworkspace: YOUR_WORKSPACE\n")
    r = _run("--config", cfg_path, "validate", "x.xlsx", cwd=SCRIPTS)
    assert r.returncode != 0
    out = r.stdout + r.stderr
    assert "缺少以下信息" in out
    assert "工作区" in out and "团队 ID" in out
    assert "setup-config" not in out


def test_stats_missing_repos_natural_language():
    """stats 未配置仓库时：非交互环境自然语言提示提供仓库路径。"""
    tmp = tempfile.mkdtemp(prefix="rdc-stats-")
    cfg_path = os.path.join(tmp, "rdc-config.yaml")
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write("repos: []\n")
    r = _run("--config", cfg_path, "stats", cwd=SCRIPTS)
    assert r.returncode != 0
    out = r.stdout + r.stderr
    assert "尚未提供待统计的 git 仓库路径" in out
    assert "请提供仓库路径" in out


def test_update_status_requires_confirm():
    """update-status 默认需确认：拒绝/非交互不调用接口；--yes 才执行；非法状态提前报错。"""
    sys.path.insert(0, SCRIPTS)
    import io
    import contextlib
    from rdc import api, cli

    tmp = tempfile.mkdtemp(prefix="rdc-updstatus-")
    auth_path = os.path.join(tmp, "auth.json")
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump({"headers": {}, "fetched_at": "2026-09-02 10:00:00"}, f)
    cfg_path = os.path.join(tmp, "rdc-config.yaml")
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(
            f"auth_file: {auth_path}\n"
            "workspace: P22TEST0000001\nproject_id: P\nteam_id: T\n"
            "tenant_id: 20001\napi_key: K\nassignee_emp_no: E\n"
            "assignee_name: N\nteam_name: M\n")

    class Args:
        ids = "P22TEST0000001-6864,P22TEST0000001-6865"
        file = None
        status = "处理中"
        dry_run = False
        yes = False
        config = cfg_path

    orig_auth, orig_update, orig_confirm = (
        cli._auth, api.update_work_items_state, cli._confirm)
    calls = {"update": 0}

    def fake_update(cfg, a, ids, status):
        calls["update"] += 1
        return {"succeededItems": [{"id": i} for i in ids], "failedItems": []}

    cli._auth = lambda args: {"headers": {}}
    api.update_work_items_state = fake_update
    try:
        # 拒绝确认 → 不调用接口
        cli._confirm = lambda q, default=False: False
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.cmd_update_status(Args())
        assert "已取消" in buf.getvalue()
        assert calls["update"] == 0
        # 确认 y → 调用接口
        cli._confirm = lambda q, default=False: True
        with contextlib.redirect_stdout(io.StringIO()):
            cli.cmd_update_status(Args())
        assert calls["update"] == 1
        # --yes → 不询问直接执行
        Args.yes = True
        with contextlib.redirect_stdout(io.StringIO()):
            cli.cmd_update_status(Args())
        assert calls["update"] == 2
        # 状态不在状态流 → 提前报错
        Args.yes = False
        Args.status = "已归档"
        try:
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                cli.cmd_update_status(Args())
            raise AssertionError("非法状态应中止")
        except SystemExit as e:
            assert "不在状态流" in str(e)
        assert calls["update"] == 2
    finally:
        cli._auth, api.update_work_items_state, cli._confirm = (
            orig_auth, orig_update, orig_confirm)


def test_setup_config_no_input_noninteractive():
    """setup-config --no-input 在非交互环境可直接写入全局配置；缺 --no-input 时优雅报错。"""
    if os.name == "nt":
        return  # Windows 路径用 %APPDATA%，此处仅覆盖 POSIX
    tmp = tempfile.mkdtemp(prefix="rdc-setup-")
    env = dict(os.environ, HOME=tmp)
    # --no-input（不带 --yes）应成功写入，而不是 EOFError 崩溃
    r = subprocess.run(
        [sys.executable, "rdc_workflow", "setup-config", "--no-input",
         "--workspace", "W1", "--team-id", "T1"],
        cwd=SCRIPTS, capture_output=True, text=True, timeout=120, env=env)
    assert r.returncode == 0, r.stderr
    cfg_path = os.path.join(tmp, ".config", "rdc-work-items.yaml")
    assert os.path.exists(cfg_path)
    assert "workspace: W1" in open(cfg_path, encoding="utf-8").read()
    # 非交互但忘了 --no-input → 明确提示而非 EOFError 堆栈
    r2 = subprocess.run(
        [sys.executable, "rdc_workflow", "setup-config", "--workspace", "W2"],
        cwd=SCRIPTS, capture_output=True, text=True, timeout=120, env=env)
    assert r2.returncode != 0
    assert "EOFError" not in r2.stderr
    out = r2.stdout + r2.stderr
    assert "--no-input" in out and "--yes" in out


def test_flow_resume_state_helpers():
    """续跑状态：reached 持久化、状态流一致性校验、无文件回退。"""
    sys.path.insert(0, SCRIPTS)
    from rdc import cli
    tmp = tempfile.mkdtemp(prefix="rdc-resume-")
    flow = ["新建", "处理中", "已完成", "已关闭"]
    cli._save_flow_ids(tmp, ["A-1", "A-2"], flow, reached=2)
    st = cli._load_flow_state(tmp)
    assert st["ids"] == ["A-1", "A-2"]
    assert st["reached"] == 2
    assert st["status_flow"] == flow
    ids, reached = cli._resume_from_state(tmp, flow)
    assert ids == ["A-1", "A-2"] and reached == 2
    # 状态流与当前配置不一致 → 拒绝续跑
    try:
        cli._resume_from_state(tmp, ["新建", "处理中", "已完成"])
        raise AssertionError("状态流不一致应拒绝续跑")
    except SystemExit as e:
        assert "不一致" in str(e)
    # 无续跑文件 → (None, 0)
    assert cli._resume_from_state(os.path.join(tmp, "empty"), flow) == (None, 0)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("cli tests passed")
