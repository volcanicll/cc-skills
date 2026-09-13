# -*- coding: utf-8 -*-
"""纯标准库 HTTP 客户端：JSON / multipart 上传 / 下载。

替代 requests，仅依赖 urllib.request / uuid / json。
"""
import json
import uuid
import urllib.error
import urllib.request


class HttpError(Exception):
    """HTTP 非 2xx 响应。body 为原始字节。"""

    def __init__(self, status, body):
        self.status = status
        self.body = body
        super().__init__(f"HTTP {status}: {body[:200]!r}")


def _open(req, timeout):
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        raise HttpError(e.code, e.read())


def _json_loads(raw):
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise HttpError(0, raw[:200]) from exc


def request_json(method, url, headers=None, payload=None, timeout=60):
    """发送 JSON 请求（method 为 GET/POST/PUT...），返回解析后的 JSON。

    与 requests.json= 对齐：payload 非空时自动设置 Content-Type: application/json
    （调用方未显式指定时），避免平台按其它类型解析请求体。
    """
    headers = dict(headers or {})
    if payload is not None and not any(k.lower() == "content-type" for k in headers):
        headers["Content-Type"] = "application/json"
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with _open(req, timeout) as resp:
        return _json_loads(resp.read())


def multipart_body(fields, files):
    """构造 multipart/form-data 报文。

    fields: {name: value}
    files:  {name: (filename, content_bytes, content_type)}
    返回 (body_bytes, boundary)。
    """
    boundary = "----rdc" + uuid.uuid4().hex
    buf = bytearray()
    for name, value in fields.items():
        buf += (f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n").encode("utf-8")
    for name, (filename, content, ctype) in files.items():
        buf += (f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"; '
                f'filename="{filename}"\r\n'
                f"Content-Type: {ctype}\r\n\r\n").encode("utf-8")
        buf += content
        buf += b"\r\n"
    buf += f"--{boundary}--\r\n".encode("utf-8")
    return bytes(buf), boundary


def post_multipart(url, headers=None, fields=None, files=None, timeout=300):
    """multipart 上传，返回解析后的 JSON。"""
    body, boundary = multipart_body(fields or {}, files or {})
    h = dict(headers or {})
    h["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    h["Content-Length"] = str(len(body))
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    with _open(req, timeout) as resp:
        return _json_loads(resp.read())


def get_bytes(url, headers=None, timeout=300):
    """GET 下载，返回原始字节。"""
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    with _open(req, timeout) as resp:
        return resp.read()
