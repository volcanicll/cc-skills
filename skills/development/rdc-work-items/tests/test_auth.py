# -*- coding: utf-8 -*-
"""auth（CDP 鉴权提取）测试：python3 tests/test_auth.py

回归保护：auth.fetch_auth 必须按「CDP.call 已展开 result」的结构解析
（getTargets 返回 {targetInfos:...}、attachToTarget 返回 {sessionId:...}、
getAllCookies 返回 {cookies:...}、evaluate 返回 {result:{value:...}}）。
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from rdc import auth

CFG = {
    "api_key": "rdc_k",
    "tenant_id": "20001",
    "assignee_emp_no": "srd_emp",
    "project_id": "9592",
    "team_id": "bdv_33380",
    "workspace": "P22CQQYYF0016",
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
                 "url": "https://www.srdcloud.cn/zxwim/9592/allWorkItems?teamId=bdv_33380"},
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
                               "value": json.dumps({"local": {"EO_SPACE_KEY": "9592"}, "session": {}})}}
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
    assert a["project_id"] == "9592"
    assert a["team_id"] == "bdv_33380"
    assert a["headers"]["x-api-key"] == "rdc_k"
    assert a["headers"]["x-auth-value"] == "tok123"
    assert a["headers"]["x-emp-no"] == "srd_emp"
    assert a["headers"]["x-project-id"] == "9592"
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


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("auth tests passed")
