# -*- coding: utf-8 -*-
"""auth（CDP 鉴权提取）测试：python3 tests/test_auth.py

回归保护：auth.fetch_auth 必须按「CDP.call 已展开 result」的结构解析
（getTargets 返回 {targetInfos:...}、attachToTarget 返回 {sessionId:...}、
getAllCookies 返回 {cookies:...}、evaluate 返回 {result:{value:...}}）。
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from rdc import auth

CFG = {
    "api_key": "rdc_k",
    "tenant_id": "20001",
    "assignee_emp_no": "srd_emp",
    "project_id": "12345",
    "team_id": "test_team_001",
    "workspace": "P22TEST0000001",
}


class FakeCDP:
    def __init__(self, ws_url):
        pass

    def close(self):
        pass

    def send(self, method, params=None, session_id=None, timeout=30):
        if method == "Target.getTargets":
            return {"targetInfos": [
                {"type": "page", "targetId": "T1",
                 "url": "https://www.srdcloud.cn/zxwim/12345/allWorkItems?teamId=test_team_001"},
                {"type": "page", "targetId": "T2", "url": "https://opencode.ai/workspace/x"},
            ]}
        if method == "Target.attachToTarget":
            return {"sessionId": "S1"}
        if method == "Network.getAllCookies":
            return {"cookies": [
                {"name": "prodtoken", "value": "tok123", "domain": ".srdcloud.cn"},
                {"name": "CTWIMAPPDPGSSOUser", "value": "srd_emp", "domain": ".srdcloud.cn"},
            ]}
        if method == "Runtime.evaluate":
            return {"result": {"type": "string",
                               "value": json.dumps({"local": {"EO_SPACE_KEY": "12345"}, "session": {}})}}
        return {}


def test_fetch_auth_parses_result():
    orig = auth.CDP
    auth.CDP = FakeCDP
    try:
        a = auth.fetch_auth(CFG, ws_url="ws://127.0.0.1:1/devtools/browser/x")
    finally:
        auth.CDP = orig
    assert a["emp_no"] == "srd_emp"
    assert a["auth_value"] == "tok123"
    assert a["project_id"] == "12345"
    assert a["team_id"] == "test_team_001"
    assert a["headers"]["x-api-key"] == "rdc_k"
    assert a["headers"]["x-auth-value"] == "tok123"
    assert a["headers"]["x-emp-no"] == "srd_emp"
    assert a["headers"]["x-project-id"] == "12345"
    assert a["headers"]["x-tenant-id"] == "20001"
    assert a["cookie_header"] and "prodtoken=tok123" in a["cookie_header"]


def test_fetch_auth_no_page_raises():
    class NoPageCDP(FakeCDP):
        def send(self, method, params=None, session_id=None, timeout=30):
            if method == "Target.getTargets":
                return {"targetInfos": [{"type": "page", "url": "https://example.com"}]}
            return {}

    orig = auth.CDP
    auth.CDP = NoPageCDP
    try:
        try:
            auth.fetch_auth(CFG, ws_url="ws://127.0.0.1:1/devtools/browser/x")
            raise AssertionError("应抛出未找到页面错误")
        except RuntimeError as e:
            assert "srdcloud.cn" in str(e)
    finally:
        auth.CDP = orig

def test_auth_is_stale():
    assert auth.auth_is_stale({"fetched_at": "2020-01-01 00:00:00"}, 12) is True
    assert auth.auth_is_stale({"fetched_at": __import__("time").strftime("%Y-%m-%d %H:%M:%S")}, 12) is False
    assert auth.auth_is_stale({}, 12) is True
    assert auth.auth_is_stale({"fetched_at": "bad"}, 12) is True


def test_manual_auth_parses_cookie():
    cookie = ("prodtoken=tok123; CTWIMAPPDPGSSOUser=srd_emp; "
              "CTWIMAPPDPGSSOCookie=c2; other=1")
    a = auth.manual_auth(CFG, cookie=cookie, auth_value=None, emp_no=None)
    assert a["auth_value"] == "tok123"
    assert a["emp_no"] == "srd_emp"
    assert a["headers"]["x-auth-value"] == "tok123"
    assert a["headers"]["x-emp-no"] == "srd_emp"
    assert a["source"] == "manual"
    # 显式覆盖
    a2 = auth.manual_auth(CFG, cookie=cookie, auth_value="override", emp_no="e2")
    assert a2["auth_value"] == "override" and a2["emp_no"] == "e2"


def test_find_browser_returns_str_or_none():
    p = auth.find_browser({"browser": "auto", "chrome_path": ""})
    assert p is None or isinstance(p, str)


def test_profile_in_use():
    tmp = tempfile.mkdtemp(prefix="rdc-prof-")
    assert auth._profile_in_use(tmp) is False
    open(os.path.join(tmp, "SingletonLock"), "w").close()
    assert auth._profile_in_use(tmp) is True


def test_save_auth_private_mode_and_default_path():
    """auth.json 必须 0600 落盘，且默认路径不得落在仓库/包目录内。"""
    import stat
    pkg_dir = os.path.dirname(auth.__file__)
    assert not auth.AUTH_FILE.startswith(pkg_dir),         f"默认鉴权路径 {auth.AUTH_FILE} 落在包目录内，有误提交风险"
    assert auth.AUTH_FILE.endswith(os.path.join("rdc-work-items", "auth.json")), auth.AUTH_FILE

    tmp = tempfile.mkdtemp(prefix="rdc-auth-mode-")
    path = os.path.join(tmp, "auth.json")
    auth.save_auth({"headers": {"x-api-key": "k"}, "cookie_header": "a=b"}, path)
    if os.name != "nt":
        mode = stat.S_IMODE(os.stat(path).st_mode)
        assert mode == 0o600, f"期望 0600，实际 {oct(mode)}"
    loaded = auth.load_auth(path)
    assert loaded["headers"]["x-api-key"] == "k"


def test_pick_free_port_avoids_busy_port():
    """pick_free_port：空闲端口原样返回；被占用时顺延到空闲端口。"""
    import socket

    def free_port():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        return port

    free = free_port()
    assert auth.pick_free_port(free) == free
    busy = free_port()
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", busy))
    listener.listen(1)
    try:
        chosen = auth.pick_free_port(busy)
        assert chosen != busy and chosen > busy
    finally:
        listener.close()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("auth tests passed")
