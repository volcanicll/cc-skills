# -*- coding: utf-8 -*-
"""net（纯标准库 HTTP 客户端）测试：python3 tests/test_net.py"""
import io
import json
import os
import sys
import urllib.error
from contextlib import contextmanager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "rdc"))

import net


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@contextmanager
def _patch_urlopen(handler):
    import urllib.request
    orig = urllib.request.urlopen
    calls = []

    def fake(req, timeout=None):
        calls.append(req)
        return handler(req)

    urllib.request.urlopen = fake
    try:
        yield calls
    finally:
        urllib.request.urlopen = orig


def test_request_json_post():
    seen = {}

    def handler(req):
        seen["method"] = req.get_method()
        seen["headers"] = dict(req.header_items())
        seen["body"] = req.data
        return FakeResp(json.dumps({"code": {"code": "0000"}, "bo": {"ok": 1}}).encode())

    with _patch_urlopen(handler) as calls:
        out = net.request_json("POST", "https://api/x", {"x-auth-value": "abc"},
                               payload={"a": 1, "b": "中文"}, timeout=30)
    assert out["bo"]["ok"] == 1
    assert seen["method"] == "POST"
    assert seen["headers"]["X-auth-value"] == "abc"
    assert json.loads(seen["body"].decode()) == {"a": 1, "b": "中文"}
    assert calls[0].full_url == "https://api/x"


def test_multipart_body():
    body, boundary = net.multipart_body(
        {"importHtmlField": "true", "teamId": "bdv_33380"},
        {"file": ("a.xlsx", b"PK\x03\x04binary", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    text = body.decode("utf-8")
    assert boundary in text
    assert 'name="importHtmlField"' in text
    assert 'name="teamId"' in text
    assert 'name="file"; filename="a.xlsx"' in text
    assert b"PK\x03\x04binary" in body
    assert text.endswith(f"--{boundary}--\r\n")
    # 2 个字段 + 1 个文件 = 3 个 part 边界 + 1 结束
    assert text.count(boundary) == 4


def test_post_multipart():
    seen = {}

    def handler(req):
        seen["ct"] = req.get_header("Content-type")
        seen["cl"] = req.get_header("Content-length")
        return FakeResp(json.dumps({"ok": 1}).encode())

    with _patch_urlopen(handler):
        out = net.post_multipart("https://api/import", headers={"x-a": "1"},
                                 fields={"k": "v"}, files={"f": ("x.bin", b"data", "application/octet-stream")})
    assert out == {"ok": 1}
    assert "multipart/form-data; boundary=" in seen["ct"]
    assert int(seen["cl"]) > 0


def test_http_error():
    def handler(req):
        raise urllib.error.HTTPError(req.full_url, 500, "err", {}, io.BytesIO(b"oops"))

    with _patch_urlopen(handler):
        try:
            net.request_json("GET", "https://api/x")
            raise AssertionError("应抛出 HttpError")
        except net.HttpError as e:
            assert e.status == 500
            assert b"oops" in e.body


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("net tests passed")
