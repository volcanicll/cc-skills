# -*- coding: utf-8 -*-
"""通过 CDP 从已登录的浏览器提取研发云鉴权数据（cookie + 自定义头）。

纯标准库：WebSocket 用内置 ws.py（RFC 6455，不发送 Origin 头），
HTTP 探测用 urllib.request。不依赖任何 pip 包。

鉴权获取支持三种方式（auth 命令按需选择）：
1. 复用已开调试端口的浏览器（DevToolsActivePort / HTTP 探测，自动发现）；
2. 自动启动带调试端口的浏览器（auth --no-launch 可关闭）：优先复用配置的
   用户配置目录（保持登录态），占用中则回退到独立配置目录，等待完成登录；
3. 手动粘贴 Cookie（auth --manual）：无 GUI / 无法启动浏览器时的兜底。
"""
import json
import os
import time
import urllib.parse
import urllib.request

from . import config
from . import ws

# 鉴权文件与 config.DEFAULTS["auth_file"] 保持同源（~/.config/rdc-work-items/auth.json），
# 禁止落在仓库/工作区内，避免活 Cookie 被误提交。
AUTH_FILE = os.path.join(config.user_config_dir(), "auth.json")
DOMAIN_FILTER = ("srdcloud.cn",)
PAGE_URL = "https://www.srdcloud.cn"


class CDP:
    """极简 CDP 客户端（浏览器级 WebSocket，纯标准库）。"""

    def __init__(self, ws_url, timeout=15):
        self._conn = ws.WebSocket(ws_url, timeout=timeout)
        self._cdp = ws.CDP(self._conn)

    def send(self, method, params=None, session_id=None, timeout=30):
        return self._cdp.call(method, params, session_id=session_id, timeout=timeout)

    def close(self):
        try:
            self._cdp.close()
        except Exception:
            pass


def _active_port_candidates(cfg):
    """按操作系统返回可能的 DevToolsActivePort 候选路径（Chrome/Edge）。"""
    import platform
    cands = []
    explicit = cfg.get("chrome_profile_dir")
    if explicit:
        cands.append(os.path.join(os.path.expanduser(explicit), "DevToolsActivePort"))
    sysname = platform.system()
    if sysname == "Windows":
        local = os.environ.get("LOCALAPPDATA", "")
        base = local or os.path.expanduser(r"~\AppData\Local")
        cands += [
            os.path.join(base, "Google", "Chrome", "User Data", "DevToolsActivePort"),
            os.path.join(base, "Microsoft", "Edge", "User Data", "DevToolsActivePort"),
        ]
    elif sysname == "Darwin":
        cands += [
            os.path.expanduser("~/Library/Application Support/Google/Chrome/DevToolsActivePort"),
            os.path.expanduser("~/Library/Application Support/Microsoft Edge/DevToolsActivePort"),
        ]
    else:  # Linux
        cands += [
            os.path.expanduser("~/.config/google-chrome/DevToolsActivePort"),
            os.path.expanduser("~/.config/microsoft-edge/DevToolsActivePort"),
        ]
    return cands


def _probe_http(port, timeout=2.0):
    """HTTP 探测 /json/version，返回浏览器级 WebSocket 地址（无则 None）。"""
    url = f"http://127.0.0.1:{port}/json/version"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        wsu = data.get("webSocketDebuggerUrl")
        return wsu or None
    except Exception:
        return None


def discover_ws_url(cfg, port=None, ws_path=None):
    """发现浏览器级 WebSocket 地址（跨平台）。

    优先级：显式 DevToolsActivePort → 配置目录 → 系统默认目录 →
    显式 chrome_debug_port 的 HTTP 探测（对应 --remote-debugging-port 启动方式）。
    """
    if port is None or ws_path is None:
        last_err = None
        for active in _active_port_candidates(cfg):
            try:
                with open(active) as f:
                    port = f.readline().strip()
                    ws_path = f.readline().strip()
                if port:
                    break
            except OSError as e:
                last_err = e
        if port and ws_path:
            return f"ws://127.0.0.1:{port}{ws_path}"
        # 兜底：HTTP 探测显式调试端口（Chrome/Edge --remote-debugging-port=9222）
        probe_port = cfg.get("chrome_debug_port") or 9222
        wsu = _probe_http(probe_port)
        if wsu:
            return wsu
        raise RuntimeError(
            f"未找到已开启调试的浏览器（最后尝试 {last_err}）。"
            "请确认浏览器已开启调试模式，或允许自动启动浏览器完成登录；"
            "也可以选择手动粘贴 Cookie 的方式。")
    if not port:
        raise RuntimeError("DevToolsActivePort 为空，请确认浏览器已开启远程调试端口")
    return f"ws://127.0.0.1:{port}{ws_path}"


# ---------------------------------------------------------------------------
# 浏览器自动探测 / 自动启动（尽量无感）
# ---------------------------------------------------------------------------

def find_browser(cfg):
    """按配置（browser/chrome_path）与操作系统探测 Chrome/Edge/Chromium 可执行文件。"""
    import platform
    import shutil
    choice = str(cfg.get("browser", "auto")).lower()
    explicit = cfg.get("chrome_path", "")
    if explicit and os.path.exists(os.path.expanduser(explicit)):
        return os.path.expanduser(explicit)
    sysname = platform.system()
    cands = []
    if sysname == "Darwin":
        cands = [
            ("chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            ("edge", "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
            ("chromium", "/Applications/Chromium.app/Contents/MacOS/Chromium"),
        ]
    elif sysname == "Windows":
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        local = os.environ.get("LOCALAPPDATA", os.path.expanduser(r"~\AppData\Local"))
        cands = [
            ("chrome", os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe")),
            ("chrome", os.path.join(pf86, "Google", "Chrome", "Application", "chrome.exe")),
            ("chrome", os.path.join(local, "Google", "Chrome", "Application", "chrome.exe")),
            ("edge", os.path.join(pf86, "Microsoft", "Edge", "Application", "msedge.exe")),
            ("edge", os.path.join(pf, "Microsoft", "Edge", "Application", "msedge.exe")),
            ("chromium", os.path.join(local, "Chromium", "Application", "chrome.exe")),
        ]
    else:  # Linux
        for name in ("google-chrome", "google-chrome-stable", "chromium",
                     "chromium-browser", "microsoft-edge"):
            p = shutil.which(name)
            if p:
                cands.append((name, p))
    for name, path in cands:
        if choice not in ("auto", name):
            continue
        if os.path.exists(path):
            return path
    return None


def _profile_in_use(profile_dir):
    """Chrome/Edge 运行时会锁定配置目录，据此判断是否被占用。"""
    if not os.path.isdir(profile_dir):
        return False
    return any(os.path.exists(os.path.join(profile_dir, n))
               for n in ("SingletonLock", "SingletonSocket", "SingletonCookie"))


def pick_free_port(preferred):
    """若 preferred 端口已被占用则顺延找空闲端口，避免误连他人调试实例。"""
    import socket
    for port in range(int(preferred or 9222), int(preferred or 9222) + 100):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.settimeout(0.3)
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        finally:
            s.close()
    return int(preferred or 9222)  # 全被占用时按原端口尝试，让启动失败显性报错


def launch_debug_browser(cfg, page_url=PAGE_URL):
    """自动启动带调试端口的浏览器并打开研发云页面。

    优先复用配置的 chrome_profile_dir（保持登录态，但需该目录未被占用）；
    占用或未配置时回退到独立配置目录（首次需登录一次，之后自动保持）。
    端口会避开已被占用的调试端口（防止误连他人调试实例）。
    返回 {"browser","profile","port"}。
    """
    import subprocess
    binary = find_browser(cfg)
    if not binary:
        raise RuntimeError(
            "未找到可用的 Chrome/Edge/Chromium 浏览器。"
            "请提供浏览器可执行文件路径，或选择手动粘贴 Cookie 的方式完成登录。")
    port = pick_free_port(int(cfg.get("chrome_debug_port") or 9222))
    configured = cfg.get("chrome_profile_dir", "")
    if configured and not _profile_in_use(os.path.expanduser(configured)):
        profile = os.path.expanduser(configured)
    else:
        profile = os.path.join(config.user_config_dir(), "browser-profile")
        if configured:
            print(f"⚠ 配置的浏览器配置目录正在使用中，改用独立配置目录：{profile}")
    os.makedirs(profile, exist_ok=True)
    cmd = [binary, f"--remote-debugging-port={port}",
           f"--user-data-dir={profile}",
           "--no-first-run", "--no-default-browser-check", page_url]
    flags = 0
    if os.name == "nt":
        flags = (getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                 | getattr(subprocess, "DETACHED_PROCESS", 0) | 0x00000008)
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     creationflags=flags)
    return {"browser": binary, "profile": profile, "port": port}


def wait_for_debug_port(cfg, timeout=60):
    """启动后轮询发现调试浏览器（DevToolsActivePort + HTTP 探测），返回 WebSocket 地址。"""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            return discover_ws_url(cfg)
        except RuntimeError as e:
            last = e
            time.sleep(0.5)
    raise RuntimeError(f"等待 {timeout}s 后仍未发现调试浏览器（{last}）")


# ---------------------------------------------------------------------------
# 提取 / 手动兜底 / 过期检测
# ---------------------------------------------------------------------------

def _find_page(cdp):
    targets = cdp.send("Target.getTargets").get("targetInfos", [])
    return next((t for t in targets if t["type"] == "page" and "srdcloud.cn" in t.get("url", "")), None)


def _extract(cdp, cfg, page):
    """从指定页面 target 提取鉴权数据；未登录（缺 auth_value/emp_no）时返回 None。"""
    page_url = page["url"]
    sid = cdp.send("Target.attachToTarget", {"targetId": page["targetId"], "flatten": True})["sessionId"]
    ck = cdp.send("Network.getAllCookies", {}, session_id=sid)
    cookies = [c for c in ck.get("cookies", [])
               if any(d in c.get("domain", "") for d in DOMAIN_FILTER)]

    expr = ("JSON.stringify({local:Object.fromEntries(Object.entries(localStorage)),"
            "session:Object.fromEntries(Object.entries(sessionStorage))})")
    r = cdp.send("Runtime.evaluate", {"expression": expr, "returnByValue": True}, session_id=sid)
    storage = json.loads(r.get("result", {}).get("result", {}).get("value") or "{}")
    local = storage.get("local", {}) or {}

    def cookie_val(name):
        return next((c["value"] for c in cookies if c["name"] == name), "")

    auth_value = cookie_val("prodtoken") or cookie_val("CTWIMAPPDPGSSOCookie")
    emp_no = cookie_val("CTWIMAPPDPGSSOUser") or cfg.get("assignee_emp_no", "")
    project_id = local.get("EO_SPACE_KEY", "") or cfg.get("project_id", "")
    team_id = (urllib.parse.parse_qs(urllib.parse.urlparse(page_url).query)
               .get("teamId", [""])[0] or cfg.get("team_id", ""))

    if not auth_value or not emp_no:
        return None
    headers = {
        "x-api-key": cfg.get("api_key", ""),
        "x-auth-value": auth_value,
        "x-emp-no": emp_no,
        "x-lang-id": "zh_CN",
        "x-tenant-id": cfg.get("tenant_id", "20001"),
        "x-device": "PC",
        "x-frame-origin": "https://www.srdcloud.cn/rdcloud",
        "x-project-id": project_id,
    }
    return {
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "workspace": cfg.get("workspace", ""),
        "team_id": team_id,
        "project_id": project_id,
        "headers": headers,
        "cookie_header": "; ".join(f"{c['name']}={c['value']}" for c in cookies),
        "cookies": {c["name"]: c["value"] for c in cookies},
        "emp_no": emp_no,
        "auth_value": auth_value,
        "source": "cdp",
    }


def fetch_auth(cfg, ws_url=None, wait_login=0):
    """连接浏览器 → 定位 srdcloud.cn 页面 → 提取 cookies / localStorage → 组装请求头。

    wait_login>0 时：未找到页面或未登录会持续等待（用于自动启动后的首次登录）。
    """
    if ws_url is None:
        ws_url = discover_ws_url(cfg)
    cdp = CDP(ws_url)
    try:
        deadline = time.time() + max(0, wait_login)
        while True:
            page = _find_page(cdp)
            if page is None:
                if time.time() < deadline:
                    print("⏳ 等待打开研发云页面…（若已弹出浏览器，请完成登录）")
                    time.sleep(2)
                    continue
                raise RuntimeError("未在浏览器中找到 srdcloud.cn 页面，请登录研发云并打开工作项页面")
            auth = _extract(cdp, cfg, page)
            if auth is not None:
                return auth
            if time.time() >= deadline:
                raise RuntimeError(
                    "鉴权数据不完整（缺少 auth_value/emp_no），请确认已在打开的浏览器中登录研发云")
            print("⏳ 检测到未登录，请在弹出的浏览器窗口中完成登录…")
            time.sleep(3)
    finally:
        cdp.close()


def manual_auth(cfg, cookie=None, auth_value=None, emp_no=None):
    """手动模式：粘贴浏览器 Cookie 头（F12 → Network → 任意 srdcloud.cn 请求）。

    缺省字段会交互式询问；cookie 与 auth_value/emp_no 可由 flags 直接传入。
    """
    if not cookie:
        cookie = input("请粘贴 Cookie 头（浏览器 F12 → Network → 任意 srdcloud.cn 请求的 Cookie）: ").strip()
    cookies = {}
    for part in cookie.split(";"):
        if "=" in part:
            k, v = part.strip().split("=", 1)
            cookies[k.strip()] = v.strip()
    auth_value = auth_value or cookies.get("prodtoken") or cookies.get("CTWIMAPPDPGSSOCookie")
    emp_no = emp_no or cookies.get("CTWIMAPPDPGSSOUser") or cfg.get("assignee_emp_no", "")
    if not auth_value:
        auth_value = input("x-auth-value（prodtoken 或 CTWIMAPPDPGSSOCookie 的值）: ").strip()
    if not emp_no:
        emp_no = input("员工号（x-emp-no）: ").strip()
    if not auth_value or not emp_no:
        raise RuntimeError("手动鉴权信息不完整（缺少 auth_value/emp_no）")
    headers = {
        "x-api-key": cfg.get("api_key", ""),
        "x-auth-value": auth_value,
        "x-emp-no": emp_no,
        "x-lang-id": "zh_CN",
        "x-tenant-id": cfg.get("tenant_id", "20001"),
        "x-device": "PC",
        "x-frame-origin": "https://www.srdcloud.cn/rdcloud",
        "x-project-id": cfg.get("project_id", ""),
    }
    return {
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "workspace": cfg.get("workspace", ""),
        "team_id": cfg.get("team_id", ""),
        "project_id": cfg.get("project_id", ""),
        "headers": headers,
        "cookie_header": cookie,
        "cookies": cookies,
        "emp_no": emp_no,
        "auth_value": auth_value,
        "source": "manual",
    }


def auth_is_stale(auth, max_hours=12):
    """鉴权是否过期（fetched_at 距今超过 max_hours，或字段缺失）。"""
    if not auth or not auth.get("fetched_at"):
        return True
    try:
        ts = time.mktime(time.strptime(auth["fetched_at"], "%Y-%m-%d %H:%M:%S"))
    except (ValueError, TypeError, OverflowError):
        return True
    return (time.time() - ts) > max_hours * 3600


def save_auth(auth, path=AUTH_FILE):
    """保存鉴权数据（目录 0700、文件 0600，含会话 Cookie 与 API Key）。"""
    config.write_private_file(path, json.dumps(auth, ensure_ascii=False, indent=2))
    return path


def load_auth(path=AUTH_FILE):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"未找到登录信息文件 {path}。请先获取研发云登录信息，再重试本命令。")
    with open(path) as f:
        return json.load(f)
