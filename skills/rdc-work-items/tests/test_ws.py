# -*- coding: utf-8 -*-
"""ws（RFC 6455 WebSocket + CDP）测试：python3 tests/test_ws.py

用本机临时 TCP 服务器完成真实握手/掩码帧/ping-pong 往返，不依赖第三方库。
"""
import base64
import hashlib
import json
import os
import socket
import struct
import sys
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "rdc"))

import ws as wsmod

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def _recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("closed")
        buf += chunk
    return buf


def _read_http_request(sock):
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("closed")
        buf += chunk
    return buf.partition(b"\r\n\r\n")[0].decode("latin-1")


def _read_frame(sock):
    h = _recv_exact(sock, 2)
    opcode = h[0] & 0x0F
    masked = h[1] & 0x80
    n = h[1] & 0x7F
    if n == 126:
        n = struct.unpack(">H", _recv_exact(sock, 2))[0]
    elif n == 127:
        n = struct.unpack(">Q", _recv_exact(sock, 8))[0]
    mask = _recv_exact(sock, 4) if masked else None
    payload = _recv_exact(sock, n)
    if mask:
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return opcode, payload


def _send_frame(sock, payload, opcode=0x1):
    header = bytearray([0x80 | opcode])
    n = len(payload)
    if n < 126:
        header.append(n)
    elif n < 65536:
        header.append(126)
        header += struct.pack(">H", n)
    else:
        header.append(127)
        header += struct.pack(">Q", n)
    sock.sendall(bytes(header) + payload)


def _free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def ws_session(conn):
    """处理一次 WebSocket 会话：握手 → 接收客户端消息 → 发送 ping → 接收 pong → 返回响应。"""
    try:
        req = _read_http_request(conn)
        key = ""
        for ln in req.split("\r\n"):
            if ln.lower().startswith("sec-websocket-key:"):
                key = ln.split(":", 1)[1].strip()
        accept = base64.b64encode(
            hashlib.sha1((key + WS_GUID).encode()).digest()).decode()
        conn.sendall(("HTTP/1.1 101 Switching Protocols\r\n"
                      "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                      f"Sec-WebSocket-Accept: {accept}\r\n\r\n").encode("latin-1"))
        # 先收客户端消息，再发 ping 验证客户端自动回 pong，最后回响应
        opcode, payload = _read_frame(conn)
        msg = json.loads(payload.decode())
        _send_frame(conn, b"ping-data", opcode=0x9)
        opcode, payload = _read_frame(conn)
        got_pong = opcode == 0xA and payload == b"ping-data"
        resp = {"id": msg["id"],
                "result": {"got_pong": got_pong, "method": msg["method"]}}
        _send_frame(conn, json.dumps(resp, separators=(",", ":")).encode())
        try:
            _read_frame(conn)  # 客户端 close 帧
        except Exception:
            pass
    finally:
        conn.close()


def _make_client_and_server(path="/devtools/browser/abc"):
    """创建已连通的 WebSocket 客户端及测试服务端后台线程。

    优先使用 socket.socketpair()（无沙箱网络权限限制，速度快）；
    不可用时回退到 TCP 监听服务。
    """
    if hasattr(socket, "socketpair"):
        try:
            client_sock, srv_sock = socket.socketpair()
            t = threading.Thread(target=ws_session, args=(srv_sock,), daemon=True)
            t.start()
            conn = wsmod.WebSocket(f"ws://127.0.0.1{path}", timeout=5, sock=client_sock)
            return conn, t
        except OSError:
            pass

    port = _free_port()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(1)

    def _srv_thread():
        try:
            c, _ = srv.accept()
            ws_session(c)
        finally:
            srv.close()

    t = threading.Thread(target=_srv_thread, daemon=True)
    t.start()
    conn = wsmod.WebSocket(f"ws://127.0.0.1:{port}{path}", timeout=5)
    return conn, t


def test_ws_echo_and_pong():
    conn, t = _make_client_and_server("/devtools/browser/abc")
    try:
        conn.send_json({"id": 7, "method": "Test.echo", "params": {}})
        resp = conn.recv_json()
    finally:
        conn.close()
    t.join(timeout=5)
    assert resp["id"] == 7
    assert resp["result"]["got_pong"] is True
    assert resp["result"]["method"] == "Test.echo"


def test_cdp_call():
    conn, t = _make_client_and_server("/devtools/page/x")
    cdp = wsmod.CDP(conn)
    try:
        result = cdp.call("Test.echo", {"x": 1})
    finally:
        cdp.close()
    t.join(timeout=5)
    assert result["method"] == "Test.echo"
    assert result["got_pong"] is True


def test_oversized_frame_rejected():
    """声明超长（>64MB）的帧应在读取 payload 前被拒绝。"""
    import struct as _struct

    class FakeSock:
        def __init__(self, data):
            self.data = data
            self.pos = 0

        def recv(self, n):
            chunk = self.data[self.pos:self.pos + n]
            self.pos += len(chunk)
            return chunk

    w = wsmod.WebSocket.__new__(wsmod.WebSocket)
    w.sock = FakeSock(bytes([0x81, 0x7F]) + _struct.pack(">Q", 10 ** 12))
    try:
        w._recv_frame()
        raise AssertionError("超长帧应被拒绝")
    except wsmod.WebSocketError as e:
        assert "超过上限" in str(e)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("ws tests passed")
