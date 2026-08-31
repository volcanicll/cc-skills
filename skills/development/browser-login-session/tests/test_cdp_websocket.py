#!/usr/bin/env python3
"""mock CDP 端到端测试：WebSocket 握手、CDP 消息匹配、Cookie 提取、错误透传、分片重组。

纯标准库，直接运行：
    python3 tests/test_cdp_websocket.py
"""

import base64
import hashlib
import json
import socket
import struct
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import browser_cdp as bc  # noqa: E402


# ---------------------------------------------------------------------------
# mock CDP 服务（WebSocket 服务端，纯标准库）
# ---------------------------------------------------------------------------

def _srv_frame(payload, opcode=1, fin=True):
    n = len(payload)
    h = bytes([(0x80 if fin else 0x00) | opcode])
    if n < 126:
        h += bytes([n])
    elif n < 65536:
        h += bytes([126]) + struct.pack(">H", n)
    else:
        h += bytes([127]) + struct.pack(">Q", n)
    return h + payload


def _recv_frame(conn):
    h = conn.recv(2)
    if len(h) < 2:
        return None, None
    opcode, n, masked = h[0] & 0x0F, h[1] & 0x7F, h[1] & 0x80
    if n == 126:
        n = struct.unpack(">H", conn.recv(2))[0]
    elif n == 127:
        n = struct.unpack(">Q", conn.recv(8))[0]
    mask = conn.recv(4) if masked else b""
    payload = b""
    while len(payload) < n:
        chunk = conn.recv(n - len(payload))
        if not chunk:
            break
        payload += chunk
    if mask:
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return opcode, payload


COOKIES_FIXTURE = [
    {"name": "session", "value": "s3cr3t", "domain": ".github.com",
     "path": "/", "httpOnly": True, "secure": True,
     "sameSite": "None", "expires": 1893456000},
    {"name": "_gh_sess", "value": "abc123", "domain": "github.com",
     "path": "/", "httpOnly": True, "secure": True,
     "sameSite": "Lax", "expires": 0},
]


def _handle(conn):
    req = b""
    while b"\r\n\r\n" not in req:
        chunk = conn.recv(4096)
        if not chunk:
            break
        req += chunk
    key = ""
    for line in req.decode("latin-1").split("\r\n"):
        if line.lower().startswith("sec-websocket-key:"):
            key = line.split(":", 1)[1].strip()
    accept = base64.b64encode(
        hashlib.sha1((key + bc.WS_GUID).encode()).digest()).decode()
    conn.sendall(("HTTP/1.1 101 Switching Protocols\r\n"
                  "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                  "Sec-WebSocket-Accept: " + accept + "\r\n\r\n").encode())
    while True:
        opcode, payload = _recv_frame(conn)
        if opcode in (None, 8):
            break
        if opcode != 1:
            continue
        msg = json.loads(payload)
        mid, m = msg["id"], msg["method"]
        if m == "Browser.getVersion":
            result = {"product": "Chrome/151.0.0.0", "protocolVersion": "1.3"}
        elif m == "Target.createTarget":
            result = {"targetId": "mock-target-1"}
        elif m == "Target.attachToTarget":
            result = {"sessionId": "mock-session-1"}
        elif m == "Network.getCookies":
            result = {"cookies": COOKIES_FIXTURE}
        elif m == "Target.closeTarget":
            result = {"success": True}
        elif m == "Runtime.evaluate":
            expr = msg.get("params", {}).get("expression", "")
            if "readyState" in expr:
                value = "complete"
            elif "location.host" in expr:
                value = "github.com"
            else:
                value = "__TEST_UA__"
            result = {"result": {"type": "string", "value": value}}
        elif m == "No.SuchMethod":
            data = json.dumps({"id": mid, "error": {
                "code": -32601, "message": "Method not found"}}).encode()
            half = len(data) // 2
            conn.sendall(_srv_frame(data[:half], fin=False))      # 分片：第一帧
            conn.sendall(_srv_frame(data[half:], opcode=0))       # continuation
            continue
        else:
            result = {}
        conn.sendall(_srv_frame(json.dumps({"id": mid, "result": result}).encode()))
    conn.close()


def _start_mock_server():
    lsock = socket.socket()
    lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lsock.bind(("127.0.0.1", 0))
    lsock.listen(8)
    port = lsock.getsockname()[1]

    def accept_loop():
        while True:
            try:
                c, _ = lsock.accept()
            except OSError:
                break
            threading.Thread(target=_handle, args=(c,), daemon=True).start()

    threading.Thread(target=accept_loop, daemon=True).start()
    time.sleep(0.2)
    return port


# ---------------------------------------------------------------------------
# 测试用例
# ---------------------------------------------------------------------------

def main():
    port = _start_mock_server()
    url = f"ws://127.0.0.1:{port}/devtools/browser/mock"

    # 1. 基础提取：Cookie 头组装 + HttpOnly 保留
    cookies, extra = bc.extract_cookies(url, "github.com")
    hdr = bc.cookie_header(cookies)
    assert len(cookies) == 2, cookies
    assert hdr == "session=s3cr3t; _gh_sess=abc123", hdr
    assert cookies[0]["httpOnly"] is True
    print("[ok] extract_cookies 基础提取")

    # 2. with_extra：UA / localStorage 读取
    _, extra2 = bc.extract_cookies(url, "github.com", with_extra=True)
    assert extra2["ua"] == "__TEST_UA__", extra2
    print("[ok] extract_cookies with_extra")

    # 3. CDP 错误透传（分片响应）
    ws = bc.WebSocket(url)
    try:
        try:
            bc.CDP(ws).call("No.SuchMethod")
            raise SystemExit("FAIL: 应抛出 CDPError")
        except bc.CDPError as e:
            assert "Method not found" in str(e), e
        print("[ok] CDPError 透传（分片重组）")
    finally:
        ws.close()

    print("\nALL TESTS PASSED")


if __name__ == "__main__":
    main()
