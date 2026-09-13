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
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


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
    assert "2.5.0" in r.stdout


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
        return api.ValidateResult(message="预计新增 1 条", raw={"successMsg": "预计新增 1 条"})

    def fake_import(cfg, a, f, team_id=None):
        calls["import"] += 1
        return api.ImportResult(
            ids=["P22TEST0000001-6864"], succeeded=1, failed=0, report_url="",
            raw={"taskInfo": {"succeededItems": [{"data": {"1": "P22TEST0000001-6864"}}]}})

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
        return api.UpdateResult(succeeded=[{"id": i} for i in ids], failed=[])

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


def test_import_auto_prep_and_ids_out():
    """单步导入：工作量 Excel 自动转导入文件（去掉平台不支持列），成功后编号落盘供续跑。"""
    sys.path.insert(0, SCRIPTS)
    import contextlib
    import io
    from rdc import api, cli, excelgen, prepare

    tmp = tempfile.mkdtemp(prefix="rdc-auto-")
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

    # 生成工作量 Excel（含平台不支持列：更新时间/创建人/创建时间）
    src = os.path.join(tmp, "8月.xlsx")
    excelgen.build({"initial_status": "新建", "work_item_type": "任务", "task_type": "开发",
                    "assignee_name": "N", "assignee_emp_no": "E", "team_name": "M"},
                   [{"title": "工作项A", "hours": 8}], src)
    assert prepare.needs_import_prep(src) is True

    ids_json = os.path.join(tmp, "ids.json")
    called = {"validate": 0, "import": 0, "file": None}
    orig_validate, orig_import, orig_confirm = api.validate, api.import_items, cli._confirm

    def fake_validate(cfg, a, f):
        called["validate"] += 1
        header, _rows = prepare._read_rows(f)
        assert "更新时间" not in header and "创建人" not in header
        return api.ValidateResult(message="预计新增 1 条", raw={})

    def fake_import(cfg, a, f, team_id=None):
        called["import"] += 1
        called["file"] = f
        return api.ImportResult(ids=["P22TEST0000001-6864"], succeeded=1, failed=0,
                                report_url="", raw={})

    class Args:
        file = src
        yes = True
        verbose = False
        team_id = None
        ids_out = ids_json
        config = cfg_path

    cli._auth = lambda args: {"headers": {}}
    cli._confirm = lambda q, default=False: True
    api.validate, api.import_items = fake_validate, fake_import
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            cli.cmd_import(Args())
        assert called["validate"] == 1 and called["import"] == 1
        # 传给平台的是去掉不支持列后的文件
        header, _rows = prepare._read_rows(called["file"])
        assert "编号" in header and "更新时间" not in header
        # ids 文件已落盘，格式与 flow ids.json 一致
        data = json.load(open(ids_json, encoding="utf-8"))
        assert data["ids"] == ["P22TEST0000001-6864"]
        assert data["status_flow"] == ["新建", "处理中", "已完成", "已关闭"]
    finally:
        api.validate, api.import_items, cli._confirm = (
            orig_validate, orig_import, orig_confirm)


def test_import_no_auto_prep_for_update_file():
    """含编号的导出文件不自动转换（保留编号=更新已有项）。"""
    sys.path.insert(0, SCRIPTS)
    from rdc import prepare, schema, xlsx
    tmp = tempfile.mkdtemp(prefix="rdc-upd-")
    src = os.path.join(tmp, "export.xlsx")
    cols = list(schema.EXPORT_COLUMNS)
    rows = [["P22TEST0000001-6864", "T", "任务", "处理中", "N E", "", "", "", "8",
             "", "", "M", "d", "开发"]]
    xlsx.write_table(src, cols, rows, sheet_name="导出结果")
    assert prepare.needs_import_prep(src) is False


def test_update_status_ids_file_dry_run():
    """update-status --ids-file：读取 import --ids-out / flow ids.json 的编号文件。"""
    sys.path.insert(0, SCRIPTS)
    import contextlib
    import io
    from rdc import cli
    tmp = tempfile.mkdtemp(prefix="rdc-idsfile-")
    ids_json = os.path.join(tmp, "ids.json")
    with open(ids_json, "w", encoding="utf-8") as f:
        json.dump({"ids": ["A-1", "A-2"],
                   "status_flow": ["新建", "处理中", "已完成", "已关闭"], "reached": 0}, f)

    class Args:
        file = None
        ids = None
        ids_file = ids_json
        status = "处理中"
        dry_run = True
        yes = False
        config = None

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cli.cmd_update_status(Args())
    out = buf.getvalue()
    assert "A-1" in out and "A-2" in out
    assert "dry-run" in out


def test_update_status_ids_file_conflict():
    """--ids-file 与 file/--ids 二选一，同时给出应报错。"""
    sys.path.insert(0, SCRIPTS)
    from rdc import cli
    tmp = tempfile.mkdtemp(prefix="rdc-conflict-")
    ids_json = os.path.join(tmp, "ids.json")
    with open(ids_json, "w", encoding="utf-8") as f:
        json.dump({"ids": ["A-1"]}, f)

    class Args:
        file = "x.xlsx"
        ids = "A-1"
        ids_file = ids_json
        status = "处理中"
        dry_run = True
        yes = False
        config = None

    try:
        cli.cmd_update_status(Args())
        raise AssertionError("同时给出 file/--ids/--ids-file 应报错")
    except SystemExit as e:
        assert "只能二选一" in str(e)


def test_cmd_auth_scenario_1_and_deduction():
    """测试场景 1：CDP 已开启且已登录时，自动推导工作区与姓名，脱敏展示。"""
    from unittest.mock import patch, MagicMock
    from rdc import auth, config, cli
    tmp = tempfile.mkdtemp(prefix="rdc-auth-test-")
    auth_path = os.path.join(tmp, "auth.json")
    fake_cfg = dict(config.DEFAULTS, auth_file=auth_path, workspace="YOUR_WORKSPACE", assignee_name="YOUR_NAME")

    class MockCDP:
        def __init__(self, ws_url): pass
        def close(self): pass
        def send(self, method, params=None, session_id=None, timeout=30):
            if method == "Target.getTargets":
                return {"targetInfos": [{"type": "page", "targetId": "P1", "url": "https://www.srdcloud.cn/workspaces/AUTO_WS_01/workItems"}]}
            if method == "Target.attachToTarget":
                return {"sessionId": "S1"}
            if method == "Network.getAllCookies":
                return {"cookies": [
                    {"name": "prodtoken", "value": "tok_very_secret_12345678", "domain": ".srdcloud.cn"},
                    {"name": "CTWIMAPPDPGSSOUser", "value": "emp_8888", "domain": ".srdcloud.cn"}
                ]}
            if method == "Runtime.evaluate":
                return {"result": {"type": "string", "value": json.dumps({"local": {"EO_SPACE_KEY": "space_888", "userInfo": json.dumps({"name": "李四"})}})}}
            return {}

    with patch.object(auth, "discover_ws_url", return_value="ws://127.0.0.1:9222/devtools/browser/xyz"), \
         patch.object(auth, "CDP", MockCDP), \
         patch.object(cli, "_cfg", return_value=fake_cfg):
        args = MagicMock(manual=False, no_launch=False, wait=0, config=None)
        cli.cmd_auth(args)

    saved = auth.load_auth(auth_path)
    assert saved["workspace"] == "AUTO_WS_01"
    assert saved["assignee_name"] == "李四"
    assert saved["emp_no"] == "emp_8888"


def test_main_401_auto_reauth():
    """测试遇到 401/403 平台错误时，静默调用 auto_reauth 刷新凭据并自动重试。"""
    from unittest.mock import patch, MagicMock
    from rdc import auth, cli, net
    retry_called = [0]
    def mock_api_action(args):
        retry_called[0] += 1
        if retry_called[0] == 1:
            raise net.HttpError(401, b"Unauthorized token expired")

    fake_cmd_args = MagicMock(func=mock_api_action, config=None)
    with patch.object(auth, "auto_reauth", return_value={"headers": {"x-auth-value": "new_tok"}}), \
         patch("argparse.ArgumentParser.parse_args", return_value=fake_cmd_args):
        cli.main(["doctor"])
    assert retry_called[0] == 2


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("cli tests passed")
