# -*- coding: utf-8 -*-
"""通过 CDP 从已登录的 Chrome 提取研发云鉴权数据（cookie + 自定义头）。

纯标准库：WebSocket 用内置 ws.py（RFC 6455，不发送 Origin 头），
HTTP 探测用 urllib.request。不依赖任何 pip 包。
"""
import json
import os
import time
import urllib.parse
import urllib.request

from . import ws

AUTH_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "auth.json")
AUTH_FILE = os.path.abspath(AUTH_FILE)
DOMAIN_FILTER = ("srdcloud.cn",)


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
            f"未找到 DevToolsActivePort（最后尝试 {last_err}）。"
            "请确认 Chrome/Edge 以 --remote-debugging-port 启动且已登录研发云，"
            "或在 config.yaml 设置 chrome_profile_dir。")
    if not port:
        raise RuntimeError("DevToolsActivePort 为空，请确认 Chrome 已开启远程调试端口")
    return f"ws://127.0.0.1:{port}{ws_path}"


def fetch_auth(cfg, ws_url=None):
    """连接 Chrome → 定位 srdcloud.cn 页面 → 提取 cookies / localStorage → 组装请求头。"""
    if ws_url is None:
        ws_url = discover_ws_url(cfg)
    cdp = CDP(ws_url)
    try:
        targets = cdp.send("Target.getTargets").get("result", {}).get("targetInfos", [])
        page = next(
            (t for t in targets if t["type"] == "page" and "srdcloud.cn" in t.get("url", "")),
            None,
        )
        if page is None:
            raise RuntimeError("未在 Chrome 中找到 srdcloud.cn 页面，请先登录研发云并打开工作项页面")
        page_url = page["url"]
        sid = cdp.send("Target.attachToTarget", {"targetId": page["targetId"], "flatten": True})["result"]["sessionId"]

        ck = cdp.send("Network.getAllCookies", {}, session_id=sid)
        cookies = [c for c in ck.get("result", {}).get("cookies", [])
                   if any(d in c.get("domain", "") for d in DOMAIN_FILTER)]

        expr = "JSON.stringify({local:Object.fromEntries(Object.entries(localStorage)),session:Object.fromEntries(Object.entries(sessionStorage))})"
        r = cdp.send("Runtime.evaluate", {"expression": expr, "returnByValue": True}, session_id=sid)
        storage = json.loads(r.get("result", {}).get("result", {}).get("value") or "{}")
        local = storage.get("local", {}) or {}

        def cookie_val(name):
            return next((c["value"] for c in cookies if c["name"] == name), "")

        auth_value = cookie_val("prodtoken") or cookie_val("CTWIMAPPDPGSSOCookie")
        emp_no = cookie_val("CTWIMAPPDPGSSOUser") or cfg.get("assignee_emp_no", "")
        project_id = local.get("EO_SPACE_KEY", "") or cfg.get("project_id", "")
        team_id = urllib.parse.parse_qs(urllib.parse.urlparse(page_url).query).get("teamId", [""])[0] or cfg.get("team_id", "")

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
        if not auth_value or not emp_no:
            raise RuntimeError("鉴权数据不完整（缺少 auth_value/emp_no），请确认已登录研发云")

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
        }
    finally:
        cdp.close()


def save_auth(auth, path=AUTH_FILE):
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w") as f:
        json.dump(auth, f, ensure_ascii=False, indent=2)
    return path


def load_auth(path=AUTH_FILE):
    if not os.path.exists(path):
        raise FileNotFoundError(f"未找到鉴权文件 {path}，请先运行 `python -m rdc.cli auth`")
    with open(path) as f:
        return json.load(f)
