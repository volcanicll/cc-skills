# -*- coding: utf-8 -*-
"""状态流转接口（updateWorkItems/edit）测试：python3 tests/test_state_api.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from rdc import api

CFG = {
    "base_url": "https://www.srdcloud.cn/zte-rdcloud-rdc-wimbackend",
    "workspace": "P22TEST0000001",
    "team_id": "test_team_001",
    "tenant_id": "20001",
    "wic_base_url": "https://www.srdcloud.cn/zte-plm-wic-api",
    "wic_version": "V1.24.22",
    "work_item_type_key": "Task",
    "state_field_id": "63f96af738aa624d3b708445",
}
AUTH = {
    "headers": {
        "x-api-key": "k",
        "x-auth-value": "v",
        "x-emp-no": "e",
        "x-tenant-id": "20001",
    },
    "cookie_header": "a=b",
}


from contextlib import contextmanager


@contextmanager
def _patch_request_json(handler):
    orig = api.net.request_json
    calls = []

    def fake(method, url, headers=None, payload=None, timeout=60):
        calls.append((method, url, headers, payload, timeout))
        return handler(payload)

    api.net.request_json = fake
    try:
        yield calls
    finally:
        api.net.request_json = orig


def test_update_state_body():
    captured = {}

    def handler(payload):
        captured["payload"] = payload
        return {"code": {"code": "0000"}, "bo": {"succeededItems": [{"id": "x"}]}}

    with _patch_request_json(handler) as calls:
        res = api.update_work_items_state(CFG, AUTH, ["P22TEST0000001-6864", "P22TEST0000001-6865"], "已完成")

    method, url, headers, payload, timeout = calls[0]
    assert method == "PUT"
    assert url == "https://www.srdcloud.cn/zte-plm-wic-api/api/workspaces/P22TEST0000001/work_items/updateWorkItems/edit"
    assert headers["content-type"] == "application/json"
    assert headers["x-wic-version"] == "V1.24.22"
    assert headers["x-auth-value"] == "v"
    assert payload["workItems"] == [
        {"id": "P22TEST0000001-6864", "workItemTypeKey": "Task", "workspaceKey": "P22TEST0000001"},
        {"id": "P22TEST0000001-6865", "workItemTypeKey": "Task", "workspaceKey": "P22TEST0000001"},
    ]
    f = payload["fields"][0]
    assert f["key"] == "System_State"
    assert f["name"] == "状态"
    assert f["value"] == "已完成"
    assert f["multiValue"] is False
    assert f["modifyType"] == "replace"
    assert f["type"] == "state"
    assert f["fieldObj"]["id"] == "63f96af738aa624d3b708445"
    assert f["fieldObj"]["workspaceKey"] == "P22TEST0000001"
    assert f["fieldObj"]["key"] == "System_State"
    usage = f["fieldObj"]["usages"][0]
    assert usage["workItemTypeKey"] == payload["workItems"][0]["workItemTypeKey"] == "Task"
    assert res.succeeded == [{"id": "x"}]
    assert res.failed == []
    assert res.raw["succeededItems"] == [{"id": "x"}]


def test_update_state_empty_ids():
    with _patch_request_json(lambda p: {"code": {"code": "0000"}}):
        try:
            api.update_work_items_state(CFG, AUTH, [], "已完成")
            raise AssertionError("空 ids 应抛 RdcError")
        except api.RdcError as e:
            assert "没有可更新" in str(e)


def test_update_state_platform_error():
    def handler(payload):
        return {"code": {"code": "E999", "msg": "工作流不存在"}}

    with _patch_request_json(handler):
        try:
            api.update_work_items_state(CFG, AUTH, ["id1"], "已完成")
            raise AssertionError("平台错误码应抛 RdcError")
        except api.RdcError as e:
            assert "工作流不存在" in str(e)


def test_import_ids():
    # 用户提供的 importExcel 响应报文
    bo = {
        "taskInfo": {
            "failedItemsSize": 0,
            "succeededItems": [
                {"data": {"1": "P22TEST0000001-6864"}, "result": 1},
                {"data": {"1": "P22TEST0000001-6865"}, "result": 1},
            ],
            "succeededItemsSize": 2,
        }
    }
    assert api.import_ids(bo) == ["P22TEST0000001-6864", "P22TEST0000001-6865"]
    assert api.import_ids({}) == []


def test_safe_file_url_allowlist():
    """fileUrl 下载白名单：仅 https + 白名单主机，其余一律拒绝。"""
    assert api.assert_safe_file_url("https://www.srdcloud.cn/a.xlsx") is not None
    assert api.assert_safe_file_url("https://srdcloud.cn/a.xlsx") is not None
    assert api.assert_safe_file_url("https://oss.srdcloud.cn/a.xlsx") is not None
    for bad in ("http://www.srdcloud.cn/a.xlsx",
                "file:///etc/passwd",
                "https://evil.example.com/a.xlsx",
                "ftp://www.srdcloud.cn/a.xlsx"):
        try:
            api.assert_safe_file_url(bad)
            raise AssertionError(f"应拒绝 {bad}")
        except api.RdcError:
            pass
    # 自定义白名单可扩展
    assert api.assert_safe_file_url("https://cdn.mycorp.com/a.xlsx",
                                    hosts=[".mycorp.com"]) is not None


def test_download_rejects_unsafe_url():
    """download 对非白名单地址在发起请求前拒绝（含 file://）。"""
    for bad in ("file:///etc/passwd", "https://evil.example.com/a.xlsx"):
        try:
            api.download(bad, auth={"cookie_header": "a=b"})
            raise AssertionError(f"应拒绝 {bad}")
        except api.RdcError:
            pass


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("state api tests passed")
