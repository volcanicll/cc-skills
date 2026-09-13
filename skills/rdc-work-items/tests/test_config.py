# -*- coding: utf-8 -*-
"""config（多平台全局配置 / auth 路径）与 yamlio dump 测试：python3 tests/test_config.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from rdc import config
from rdc import yamlio


def test_user_config_dir_posix():
    import platform
    if os.name == "nt":
        return  # Windows 分支单独测试
    home = tempfile.mkdtemp(prefix="rdc-home-")
    old = os.environ.get("HOME")
    os.environ["HOME"] = home
    try:
        assert config.user_config_dir() == os.path.join(home, ".config", "rdc-work-items")
    finally:
        if old is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = old


def test_user_config_dir_windows():
    old_name, old_appdata = config.os.name, os.environ.get("APPDATA")
    tmp = tempfile.mkdtemp(prefix="rdc-appdata-")
    config.os.name = "nt"
    os.environ["APPDATA"] = tmp
    try:
        assert config.user_config_dir() == os.path.join(tmp, "rdc-work-items")
        assert config.global_config_path() == os.path.join(tmp, "rdc-work-items.yaml")
    finally:
        config.os.name = old_name
        if old_appdata is None:
            os.environ.pop("APPDATA", None)
        else:
            os.environ["APPDATA"] = old_appdata


def test_yamlio_dump_roundtrip():
    data = {
        "workspace": "P22TEST0000001",
        "team_id": "test_team_001",
        "tenant_id": "20001",
        "api_key": "rdc_abc",
        "assignee_name": "张三",
        "status_flow": ["新建", "处理中", "已完成"],
        "repos": ["/a/repo", "/b/repo"],
        "wic_base_url": "https://www.srdcloud.cn/zte-plm-wic-api",
        "empty": [],
        "none": None,
        "flag": True,
        "num": 8.5,
        "chrome_profile_dir": "~/Library/Application Support/Google/Chrome",
        "special#key": "值#带#井号",
    }
    text = yamlio.dump(data)
    back = yamlio.load(text)
    assert back == data, back


def test_write_global_config_and_reload():
    tmp = tempfile.mkdtemp(prefix="rdc-cfg-")
    path = os.path.join(tmp, "rdc-work-items.yaml")
    data = {"workspace": "P22TEST0000001", "team_id": "test_team_001",
            "repos": ["/a"], "status_flow": ["新建", "处理中"]}
    written = config.write_global_config(data, path)
    assert written == path and os.path.exists(path)
    loaded = yamlio.load(open(path, encoding="utf-8").read())
    assert loaded == data


def test_global_config_auto_load():
    """patch CONFIG_FILES 指向临时全局配置，验证 load_config 自动加载。"""
    tmp = tempfile.mkdtemp(prefix="rdc-cfg-")
    gpath = os.path.join(tmp, "rdc-work-items.yaml")
    config.write_global_config(
        {"workspace": "P22TEST0000001", "team_id": "test_team_001",
         "api_key": "k", "git_author": "xiangcan"}, gpath)
    old = config.CONFIG_FILES
    config.CONFIG_FILES = ["rdc-config.yaml", gpath]
    try:
        cfg = config.load_config()
        assert cfg["workspace"] == "P22TEST0000001"
        assert cfg["team_id"] == "test_team_001"
        assert cfg["api_key"] == "k"
        # DEFAULTS 兜底仍在
        assert cfg["base_url"].startswith("https://www.srdcloud.cn")
        assert cfg["auth_file"].endswith(os.path.join("rdc-work-items", "auth.json"))
    finally:
        config.CONFIG_FILES = old


def test_write_global_config_private_mode():
    """含 api_key 的全局配置必须 0600 落盘（POSIX；Windows 跳过）。"""
    import stat
    if os.name == "nt":
        return
    tmp = tempfile.mkdtemp(prefix="rdc-cfg-mode-")
    path = os.path.join(tmp, "rdc-work-items.yaml")
    config.write_global_config({"api_key": "secret", "workspace": "W"}, path)
    mode = stat.S_IMODE(os.stat(path).st_mode)
    assert mode == 0o600, f"期望 0600，实际 {oct(mode)}"


def test_default_columns_from_schema():
    """默认 excel_columns 与 schema 单一事实源一致，且无死键 domain。"""
    from rdc import schema
    assert config.DEFAULTS["excel_columns"] == list(schema.EXPORT_COLUMNS)
    assert "domain" not in config.DEFAULTS


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("config tests passed")
