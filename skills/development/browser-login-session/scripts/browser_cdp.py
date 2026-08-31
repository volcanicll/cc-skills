#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
browser_cdp.py - 通过 CDP 复用浏览器登录态（纯 Python 标准库，零第三方依赖）

为什么是 CDP + 专用 profile：
  * Cookie 的加解密全部由浏览器自己完成（Windows App-Bound、macOS Keychain、
    Linux "peanuts"），本工具不碰磁盘加密格式，天然规避 2025-2026 年
    Chrome/Edge 的 App-Bound 限制。
  * Chrome 136+ 禁止对"默认用户数据目录"开远程调试端口；chrome://inspect 的
    auto-connect 虽能用默认 profile，但每次新连接都要人工点"允许"，无法无人值守。
  * 因此本工具默认使用"专用 user-data-dir"：首次 --setup 时从真实 profile 复制
    登录态（一次性，需要日常浏览器关闭几秒），之后每次启动专用实例都带调试端口，
    全程无弹窗、可无人值守、无任何安装步骤。

依赖：Python >= 3.8 标准库。不需要 pip install、不需要 Node、不需要浏览器驱动。

常用命令：
  首次（一次性，自动复制登录态）：
    python3 browser_cdp.py github.com --setup
  之后日常：
    python3 browser_cdp.py github.com
  日常浏览器重新登录后，同步一次登录态：
    python3 browser_cdp.py github.com --resync
  额外读取 UA / client hints / localStorage / sessionStorage：
    python3 browser_cdp.py github.com --with-extra --json
  使用 Edge：
    python3 browser_cdp.py github.com --browser edge --setup
"""

import argparse
import base64
import hashlib
import json
import os
import platform
import shutil
import socket
import struct
import subprocess
import sys
import time
import urllib.parse
import urllib.request

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
DEFAULT_PORT = 9333
SKIP_DIRS = {
    "Cache", "Code Cache", "GPUCache", "DawnCache", "GrShaderCache",
    "ShaderCache", "component_crx_cache", "Crashpad", "GraphiteDawnCache",
    "optimization_guide_model_store",
}


# ---------------------------------------------------------------------------
# 浏览器定位（可执行文件 + 真实 profile 目录，按平台）
# ---------------------------------------------------------------------------

def _first_existing(paths):
    for p in paths:
        if p and os.path.isfile(p):
            return p
    return paths[0] if paths else None


def _which_first(names):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


def browser_info(browser):
    """返回 {browser, label, exe, user_data_dir}。"""
    home = os.path.expanduser("~")
    sysname = platform.system()
    if browser == "chrome":
        label = "Chrome"
        if sysname == "Darwin":
            exe = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            udd = os.path.join(home, "Library", "Application Support", "Google", "Chrome")
        elif sysname == "Windows":
            pf = os.environ.get("ProgramFiles", r"C:\Program Files")
            pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
            exe = _first_existing([
                os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(pf86, "Google", "Chrome", "Application", "chrome.exe"),
            ])
            local = os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
            udd = os.path.join(local, "Google", "Chrome", "User Data")
        else:
            exe = _which_first(["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"])
            udd = os.path.join(home, ".config", "google-chrome")
    else:  # edge
        label = "Edge"
        if sysname == "Darwin":
            exe = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
            udd = os.path.join(home, "Library", "Application Support", "Microsoft Edge")
        elif sysname == "Windows":
            pf = os.environ.get("ProgramFiles", r"C:\Program Files")
            pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
            exe = _first_existing([
                os.path.join(pf, "Microsoft", "Edge", "Application", "msedge.exe"),
                os.path.join(pf86, "Microsoft", "Edge", "Application", "msedge.exe"),
            ])
            local = os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
            udd = os.path.join(local, "Microsoft", "Edge", "User Data")
        else:
            exe = _which_first(["microsoft-edge", "microsoft-edge-stable"])
            udd = os.path.join(home, ".config", "microsoft-edge")
    return {"browser": browser, "label": label, "exe": exe, "user_data_dir": udd}


def resolve_browser(choice):
    """auto 时优先选已安装的浏览器。"""
    order = ["chrome", "edge"] if choice != "edge" else ["edge"]
    for name in order:
        info = browser_info(name)
        if choice != "auto":
            return info
        if info["exe"] and (os.path.isfile(info["exe"]) or os.path.isdir(info["user_data_dir"])):
            return info
    raise RuntimeError("未找到 Chrome/Edge，请用 --browser 指定或先安装浏览器。")


def dedicated_dir(browser):
    """专用 profile 的默认位置，所有登录态与调试实例都放这里。"""
    return os.path.join(os.path.expanduser("~"), ".browser_cdp", browser["browser"])


# ---------------------------------------------------------------------------
# 极简 WebSocket 客户端（RFC 6455，标准库实现）
# ---------------------------------------------------------------------------

class WebSocketError(Exception):
    pass


class WebSocket:
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
        expect = base64.b64encode(hashlib.sha1((key + WS_GUID).encode()).digest()).decode()
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


# ---------------------------------------------------------------------------
# CDP 调用
# ---------------------------------------------------------------------------

class CDPError(Exception):
    pass


class CDP:
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


def eval_js(cdp, session_id, expr):
    r = cdp.call("Runtime.evaluate",
                 {"expression": expr, "returnByValue": True},
                 session_id=session_id)
    res = r.get("result", {})
    return res.get("value", res.get("description"))


def wait_loaded(cdp, session_id, domain, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            state = eval_js(cdp, session_id, "document.readyState")
            host = eval_js(cdp, session_id, "location.host") or ""
        except Exception:
            state, host = None, ""
        if state == "complete" and host and domain.split(":")[0] in host:
            return True
        time.sleep(0.3)
    return False


def extract_cookies(ws_url, domain, with_extra=False, keep_tab=False, timeout=20):
    """连接浏览器级 WebSocket，读目标域 Cookie（含 HttpOnly），可选读 UA / storage。"""
    ws = WebSocket(ws_url, timeout=timeout)
    try:
        cdp = CDP(ws)
        cdp.call("Browser.getVersion", timeout=timeout)
        target = cdp.call("Target.createTarget",
                          {"url": f"https://{domain}/"}, timeout=timeout)
        target_id = target.get("targetId")
        attached = cdp.call("Target.attachToTarget",
                            {"targetId": target_id, "flatten": True}, timeout=timeout)
        session_id = attached.get("sessionId")
        try:
            urls = [f"https://{domain}/"]
            if not domain.startswith("www."):
                urls.append(f"https://www.{domain}/")
            result = cdp.call("Network.getCookies", {"urls": urls},
                              session_id=session_id, timeout=timeout)
            cookies = result.get("cookies", [])
            extra = {}
            if with_extra:
                wait_loaded(cdp, session_id, domain)
                extra["ua"] = eval_js(cdp, session_id, "navigator.userAgent")
                extra["clientHints"] = eval_js(
                    cdp, session_id,
                    "JSON.stringify(navigator.userAgentData ? {brands: navigator.userAgentData.brands, "
                    "platform: navigator.userAgentData.platform, mobile: navigator.userAgentData.mobile} : null)")
                extra["localStorage"] = eval_js(
                    cdp, session_id,
                    "JSON.stringify(Object.fromEntries(Object.entries(localStorage)))")
                extra["sessionStorage"] = eval_js(
                    cdp, session_id,
                    "JSON.stringify(Object.fromEntries(Object.entries(sessionStorage)))")
            return cookies, extra
        finally:
            if not keep_tab and target_id:
                try:
                    cdp.call("Target.closeTarget", {"targetId": target_id}, timeout=10)
                except Exception:
                    pass
    finally:
        ws.close()


def cookie_header(cookies):
    return "; ".join(f"{c['name']}={c['value']}"
                     for c in cookies if c.get("value") is not None)


def close_browser(ws_url):
    """通过 CDP 优雅关闭浏览器（用于 --close-browser / --resync）。"""
    ws = WebSocket(ws_url, timeout=10)
    try:
        CDP(ws).call("Browser.close", timeout=10)
    finally:
        ws.close()


# ---------------------------------------------------------------------------
# 端点发现与浏览器启动
# ---------------------------------------------------------------------------

def read_devtools_active_port(udd):
    """DevToolsActivePort 文件：第 1 行端口，第 2 行浏览器级 WS 路径。"""
    path = os.path.join(udd, "DevToolsActivePort")
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        if not lines:
            return None
        return int(lines[0]), lines[1] if len(lines) > 1 else None
    except Exception:
        return None


def probe_http(port, timeout=2.0):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def probe_ws(port, ws_path, timeout=3.0):
    try:
        ws = WebSocket(f"ws://127.0.0.1:{port}{ws_path}", timeout=timeout)
        ws.close()
        return True
    except Exception:
        return False


def find_endpoint(browser, port=None):
    """按优先级探测可用 CDP 端点，返回 (mode, port, ws_url) 或 None。

    优先级：显式端口 -> 专用目录(文件/HTTP) -> 真实目录(文件/HTTP)。
    Chrome 151 实测：传统模式不写 DevToolsActivePort，只能 HTTP 探测；
    auto-connect 模式写文件但 HTTP 返回 404，只能走文件里的 WS 路径。
    """
    if port:
        v = probe_http(port)
        if v and v.get("webSocketDebuggerUrl"):
            return ("http", port, v["webSocketDebuggerUrl"])

    for udd in (dedicated_dir(browser), browser["user_data_dir"]):
        active = read_devtools_active_port(udd)
        if active:
            p, ws_path = active
            if port and p != port:
                continue  # 文件属于另一个实例，显式端口优先
            if ws_path and probe_ws(p, ws_path):
                return ("file", p, f"ws://127.0.0.1:{p}{ws_path}")
            v = probe_http(p)
            if v and v.get("webSocketDebuggerUrl"):
                return ("http", p, v["webSocketDebuggerUrl"])

    if not port:
        v = probe_http(DEFAULT_PORT)
        if v and v.get("webSocketDebuggerUrl"):
            return ("http", DEFAULT_PORT, v["webSocketDebuggerUrl"])
    return None


def launch_dedicated(browser, udd, port, profile="Default", headless=False):
    exe = browser["exe"]
    if not exe or not os.path.isfile(exe):
        raise RuntimeError(f"找不到 {browser['label']} 可执行文件: {exe}")
    args = [exe,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={udd}",
            "--no-first-run",
            "--no-default-browser-check"]
    if profile != "Default":
        args.append(f"--profile-directory={profile}")
    if headless:
        args.append("--headless=new")
    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + 20
    while time.time() < deadline:
        v = probe_http(port)
        if v and v.get("webSocketDebuggerUrl"):
            return ("http", port, v["webSocketDebuggerUrl"])
        time.sleep(0.5)
    raise RuntimeError(
        f"{browser['label']} 启动后未出现调试端点（端口 {port}）。\n"
        "注意：Chrome 136+ 禁止对默认用户数据目录开调试端口，必须配合专用 "
        "--user-data-dir（本工具已自动传入）。若你手动改过目录权限，请检查。")


def is_browser_running(browser):
    sysname = platform.system()
    if sysname == "Darwin":
        name = "Google Chrome" if browser["browser"] == "chrome" else "Microsoft Edge"
        return subprocess.run(["pgrep", "-x", name],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if sysname == "Windows":
        image = "chrome.exe" if browser["browser"] == "chrome" else "msedge.exe"
        out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {image}", "/NH"],
                             capture_output=True, text=True).stdout
        return image.lower() in out.lower()
    names = {"chrome": ["chrome", "google-chrome", "chromium"],
             "edge": ["microsoft-edge"]}[browser["browser"]]
    for n in names:
        if subprocess.run(["pgrep", "-u", str(os.getuid()), "-x", n],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            return True
    return False


def quit_browser(browser, wait=12):
    """优雅退出日常浏览器（仅 --setup/--resync 复制 profile 前需要）。"""
    sysname = platform.system()
    if sysname == "Darwin":
        app = "Google Chrome" if browser["browser"] == "chrome" else "Microsoft Edge"
        subprocess.run(["osascript", "-e", f'tell application "{app}" to quit'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif sysname == "Windows":
        image = "chrome.exe" if browser["browser"] == "chrome" else "msedge.exe"
        subprocess.run(["taskkill", "/IM", image],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        names = {"chrome": ["chrome", "google-chrome", "chromium"],
                 "edge": ["microsoft-edge"]}[browser["browser"]]
        for n in names:
            subprocess.run(["pkill", "-TERM", "-u", str(os.getuid()), "-x", n],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + wait
    while time.time() < deadline:
        if not is_browser_running(browser):
            return True
        time.sleep(0.5)
    return False


# ---------------------------------------------------------------------------
# profile 复制（一次性 setup / 刷新 resync）
# ---------------------------------------------------------------------------

def copy_profile(src_udd, dst_udd, profile="Default", overwrite=False):
    """把真实 profile 的登录态（Local State + 目标 profile 目录）复制到专用目录。

    跳过 Cache 等大目录；删除复制过来的会话恢复文件，避免专用实例恢复日常标签页。
    """
    src_profile = os.path.join(src_udd, profile)
    if not os.path.isdir(src_profile):
        raise RuntimeError(f"源 profile 不存在: {src_profile}")
    dst_profile = os.path.join(dst_udd, profile)
    if not overwrite and os.path.exists(dst_profile):
        raise RuntimeError(
            f"专用目录已存在: {dst_udd}\n"
            "  如需覆盖并重新同步登录态，请改用 --resync；或 --profile-dir 指定新目录。")
    os.makedirs(dst_udd, exist_ok=True)

    src_ls = os.path.join(src_udd, "Local State")
    if os.path.isfile(src_ls):
        shutil.copy2(src_ls, os.path.join(dst_udd, "Local State"))

    if overwrite and os.path.isdir(dst_profile):
        print(f"  删除旧专用 profile: {dst_profile}")
        shutil.rmtree(dst_profile)
    ignore = lambda d, names: [n for n in names if n in SKIP_DIRS]
    shutil.copytree(src_profile, dst_profile, symlinks=True, ignore=ignore)

    # 清理会话恢复文件：专用实例不应恢复日常浏览器打开的标签页
    for name in ("Current Session", "Current Tabs", "Last Session", "Last Tabs"):
        p = os.path.join(dst_profile, name)
        if os.path.isfile(p):
            os.remove(p)
    sess_dir = os.path.join(dst_profile, "Sessions")
    if os.path.isdir(sess_dir):
        shutil.rmtree(sess_dir)
    return dst_profile


def run_setup(browser, dedicated, profile, port, headless, resync=False):
    """一次性 setup 或 resync：退出日常浏览器 -> 复制登录态 -> 启动专用调试实例。"""
    if not os.path.isdir(browser["user_data_dir"]):
        raise RuntimeError(f"未找到 {browser['label']} 的用户数据目录: {browser['user_data_dir']}")
    if resync and os.path.isdir(dedicated):
        ep = find_endpoint(browser, port)
        if ep:
            try:
                print(f"  正在关闭专用 {browser['label']} 实例…")
                close_browser(ep[2])
                time.sleep(2)
            except Exception:
                pass
    if is_browser_running(browser):
        print(f"  正在退出日常 {browser['label']}（复制登录态前需短暂关闭，请先保存工作）…")
        if not quit_browser(browser):
            raise RuntimeError("日常浏览器未能退出，请手动关闭后重试。")
    print(f"  正在复制登录态: {browser['user_data_dir']} -> {dedicated}")
    copy_profile(browser["user_data_dir"], dedicated, profile, overwrite=resync)
    print(f"  正在启动专用 {browser['label']}（端口 {port or DEFAULT_PORT}）…")
    launch_dedicated(browser, dedicated, port or DEFAULT_PORT, profile, headless)
    print("  完成。日常浏览器可以重新打开。")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv):
    ap = argparse.ArgumentParser(
        prog="browser_cdp.py",
        description="通过 CDP 复用浏览器登录态（纯标准库，零依赖）",
        epilog=(
            "示例:\n"
            "  python3 browser_cdp.py github.com --setup      # 首次：复制登录态并启动\n"
            "  python3 browser_cdp.py github.com              # 日常：取 Cookie 头\n"
            "  python3 browser_cdp.py github.com --json       # 结构化输出\n"
            "  python3 browser_cdp.py github.com --resync     # 重新同步登录态\n"
            "  python3 browser_cdp.py github.com --with-extra # 额外读 UA/localStorage\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("domain", help="目标域名，如 github.com")
    ap.add_argument("--browser", choices=["chrome", "edge", "auto"], default="auto")
    ap.add_argument("--port", type=int, default=None,
                    help="调试端口（探测与启动都用它，默认 %d）" % DEFAULT_PORT)
    ap.add_argument("--profile-dir", default=None,
                    help="专用 user-data-dir（默认 ~/.browser_cdp/<browser>）")
    ap.add_argument("--profile", default="Default",
                    help="源 profile 子目录（默认 Default，多账号可填 Profile 1）")
    ap.add_argument("--setup", action="store_true",
                    help="一次性：复制真实 profile 登录态到专用目录并启动调试实例")
    ap.add_argument("--resync", action="store_true",
                    help="重新同步登录态（覆盖专用目录，需要日常浏览器短暂关闭）")
    ap.add_argument("--no-launch", action="store_true",
                    help="找不到端点时不要自动启动浏览器")
    ap.add_argument("--headless", action="store_true",
                    help="专用实例以 headless 方式启动")
    ap.add_argument("--with-extra", action="store_true",
                    help="额外读取 UA / client hints / localStorage / sessionStorage")
    ap.add_argument("--keep-tab", action="store_true",
                    help="提取后不关闭临时标签页")
    ap.add_argument("--close-browser", action="store_true",
                    help="提取后关闭由本工具启动的浏览器实例")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    browser = resolve_browser(args.browser)
    dedicated = args.profile_dir or dedicated_dir(browser)
    port = args.port or DEFAULT_PORT

    if args.setup or args.resync:
        run_setup(browser, dedicated, args.profile, port, args.headless, resync=args.resync)

    endpoint = find_endpoint(browser, args.port)
    launched = False
    if not endpoint:
        if args.no_launch:
            raise RuntimeError("未找到可用 CDP 端点（--no-launch 已指定）")
        if not os.path.isdir(dedicated):
            raise RuntimeError(
                "未找到专用 profile 目录，也没有运行中的调试实例。\n"
                "首次使用（一次性，自动复制当前浏览器登录态）：\n"
                f"  python3 {os.path.basename(sys.argv[0])} {args.domain} --setup\n"
                "之后直接运行本命令即可。")
        print(f"[launch] 正在启动专用 {browser['label']} 实例（{port}）…")
        endpoint = launch_dedicated(browser, dedicated, port, args.profile, args.headless)
        launched = True

    try:
        cookies, extra = extract_cookies(
            endpoint[2], args.domain,
            with_extra=args.with_extra, keep_tab=args.keep_tab)
    finally:
        if args.close_browser and launched:
            try:
                close_browser(endpoint[2])
            except Exception as e:
                print(f"[warn] 关闭浏览器失败: {e}", file=sys.stderr)

    header = cookie_header(cookies)
    if args.json:
        out = {
            "domain": args.domain,
            "browser": browser["label"],
            "endpoint_mode": endpoint[0],
            "port": endpoint[1],
            "cookieCount": len(cookies),
            "cookieHeader": header,
            "cookies": [
                {"name": c.get("name"), "value": c.get("value"),
                 "domain": c.get("domain"), "path": c.get("path"),
                 "httpOnly": c.get("httpOnly"), "secure": c.get("secure"),
                 "sameSite": c.get("sameSite"),
                 "expires": c.get("expires")} for c in cookies],
        }
        if extra:
            parsed = {}
            for k, v in extra.items():
                if isinstance(v, str):
                    try:
                        parsed[k] = json.loads(v)
                    except Exception:
                        parsed[k] = v
                else:
                    parsed[k] = v
            out["extra"] = parsed
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"[ok] {browser['label']} / 端口 {endpoint[1]} / {args.domain}"
              f"（端点: {endpoint[0]}）")
        print(f"Cookie 数量: {len(cookies)}")
        print(f"Cookie 头 ({len(header)} 字节):")
        print(header)
        if extra:
            print(f"UA: {extra.get('ua')}")
            if extra.get("clientHints"):
                print(f"client hints: {extra['clientHints']}")
            for k in ("localStorage", "sessionStorage"):
                v = extra.get(k)
                if v:
                    print(f"{k}: {v[:200]}{'...' if len(v) > 200 else ''}")

    if not cookies:
        print("[warn] 未获取到任何 Cookie——该域名可能未在专用 profile 中登录。"
              "可在打开的浏览器窗口里登录一次，或重新 --resync。", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)
