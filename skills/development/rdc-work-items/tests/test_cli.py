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


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("cli tests passed")
