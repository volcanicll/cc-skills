# -*- coding: utf-8 -*-
"""纯标准库 WebSocket (RFC 6455) + 极简 CDP 客户端。

移植自 browser-login-session/scripts/browser_cdp.py 的手写实现：
不发送 Origin 头（等价 suppress_origin），规避 Chrome/Edge CDP 对带 Origin
连接的 403 拒绝。仅依赖 Python 标准库（socket/struct/base64/hashlib）。
"""
import base64
import hashlib
import json
import os
import socket
import struct
import urllib.parse

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class WebSocketError(Exception):
    pass


class WebSocket:
    """极简 WebSocket 客户端（仅 ws://，客户端帧掩码，自动应答 ping）。"""

    def __init__(self, url, timeout=15):
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "ws":
            raise WebSocketError(f"仅支持 ws:// 地址: {url}")
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 80
        self.sock = socket.create_connection((host, port), timeout=timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode("ascii"))
        resp = self._read_until(b"\r\n\r\n")
        lines = resp.decode("latin-1").split("\r\n")
        status = lines[0].split(" ", 2)
        if len(status) < 2 or status[1] != "101":
            raise WebSocketError(f"WebSocket 握手失败: {lines[0]}")
        headers = {}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        expect = base64.b64encode(
            hashlib.sha1((key + WS_GUID).encode()).digest()).decode()
        if headers.get("sec-websocket-accept") != expect:
            raise WebSocketError("Sec-WebSocket-Accept 校验失败")

    def _read_until(self, marker):
        buf = b""
        while marker not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise WebSocketError("握手期间连接被关闭")
            buf += chunk
        return buf

    def _recv_exact(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise WebSocketError("连接被关闭")
            buf += chunk
        return buf

    def send(self, payload, opcode=0x1):
        """客户端帧必须掩码。"""
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        header = bytearray([0x80 | opcode])
        n = len(payload)
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        self.sock.sendall(bytes(header) + mask + masked)

    def _recv_frame(self):
        h = self._recv_exact(2)
        fin = h[0] & 0x80
        opcode = h[0] & 0x0F
        masked = h[1] & 0x80
        n = h[1] & 0x7F
        if n == 126:
            n = struct.unpack(">H", self._recv_exact(2))[0]
        elif n == 127:
            n = struct.unpack(">Q", self._recv_exact(8))[0]
        mask = self._recv_exact(4) if masked else None
        payload = self._recv_exact(n)
        if mask:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        return bool(fin), opcode, payload

    def recv_message(self):
        """重组一条完整消息，自动应答 ping、忽略 pong。"""
        buf = b""
        while True:
            fin, opcode, payload = self._recv_frame()
            if opcode == 0x8:  # close
                raise WebSocketError("对端关闭了连接")
            if opcode == 0x9:  # ping -> pong
                self.send(payload, 0xA)
                continue
            if opcode == 0xA:  # pong
                continue
            if opcode == 0x1 or opcode == 0x2:
                buf = payload
                if fin:
                    return buf
            elif opcode == 0x0:  # continuation
                buf += payload
                if fin:
                    return buf
            else:
                raise WebSocketError(f"未知 opcode: {opcode:#x}")

    def send_json(self, obj):
        self.send(json.dumps(obj, separators=(",", ":")).encode())

    def recv_json(self):
        return json.loads(self.recv_message().decode("utf-8"))

    def close(self):
        try:
            self.send(b"", 0x8)
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass


class CDPError(Exception):
    pass


class CDP:
    """极简 CDP 客户端（浏览器级 WebSocket）。"""

    def __init__(self, ws):
        self.ws = ws
        self._id = 0

    def call(self, method, params=None, session_id=None, timeout=20):
        self._id += 1
        msg = {"id": self._id, "method": method}
        if params is not None:
            msg["params"] = params
        if session_id:
            msg["sessionId"] = session_id
        self.ws.send_json(msg)
        self.ws.sock.settimeout(timeout)
        try:
            while True:
                resp = self.ws.recv_json()
                if resp.get("id") != self._id:
                    continue  # 事件或其它响应，忽略
                if "error" in resp:
                    err = resp["error"]
                    raise CDPError(f"{method} 失败: {err.get('message', err)}")
                return resp.get("result") or {}
        finally:
            self.ws.sock.settimeout(None)

    def close(self):
        self.ws.close()
