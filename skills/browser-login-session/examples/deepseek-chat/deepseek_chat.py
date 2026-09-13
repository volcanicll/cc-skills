#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deepseek_chat.py - 通过 CDP 复用浏览器登录态调用 DeepSeek Chat API

纯 Python 标准库，依赖本 skill 核心实现 `../../scripts/browser_cdp.py`
与本目录的官方 PoW 求解模块 sha3_wasm_bg.wasm（DeepSeek 官方 DeepSeekHashV1）。

整条链路：
  1. CDP 取 chat.deepseek.com 的 Cookie + localStorage（Bearer token / hif 头）；
  2. POST /api/v0/chat/create_pow_challenge 拿 PoW 挑战；
  3. 在浏览器页面里加载官方 WASM 求解，生成 x-ds-pow-response；
  4. POST /api/v0/chat/completion，解析 CRDT 流式协议，重组回答。

用法：
  新会话：
    python3 deepseek_chat.py --new --prompt "你好"
  继续已有会话（parent_message_id 用最后一条消息 id）：
    python3 deepseek_chat.py --session-id <id> --parent-message-id <id> --prompt "..."
  查看会话历史（含思考/回答全文）：
    python3 deepseek_chat.py --session-id <id> --history
"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
import browser_cdp as bc

DOMAIN = "chat.deepseek.com"
BASE = f"https://{DOMAIN}"
WASM_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sha3_wasm_bg.wasm")
SOLVER_JS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pow_solve.mjs")


# ---------------------------------------------------------------------------
# 凭据与基础请求
# ---------------------------------------------------------------------------

def get_credentials():
    browser = bc.resolve_browser("auto")
    ep = bc.find_endpoint(browser)
    if not ep:
        raise RuntimeError("未找到 CDP 端点，请先运行 browser_cdp.py --setup 或确认浏览器调试实例在运行")
    cookies, extra = bc.extract_cookies(ep[2], DOMAIN, with_extra=True)
    ls = extra.get("localStorage") or {}
    if isinstance(ls, str):
        ls = json.loads(ls)
    return {
        "browser": browser,
        "endpoint": ep,
        "cookie_header": bc.cookie_header(cookies),
        "user_token": json.loads(ls["userToken"])["value"],
        "hif_dliq": json.loads(ls["hif_dliq_cached"]),
        "hif_leim": json.loads(ls["hif_leim_cached"]),
        "ua": extra["ua"],
    }


def base_headers(cred, referer=None):
    return {
        "accept": "*/*",
        "accept-encoding": "identity",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "authorization": f"Bearer {cred['user_token']}",
        "content-type": "application/json",
        "cookie": cred["cookie_header"],
        "origin": BASE,
        "priority": "u=1, i",
        "referer": referer or f"{BASE}/",
        "sec-ch-ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Google Chrome";v="152"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": cred["ua"],
        "x-client-bundle-id": "com.deepseek.chat",
        "x-client-locale": "en_US",
        "x-client-platform": "web",
        "x-client-timezone-offset": "28800",
        "x-client-version": "2.4.0",
        "x-hif-dliq": cred["hif_dliq"],
        "x-hif-leim": cred["hif_leim"],
    }


def http_json(method, path, headers, body=None, timeout=60):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


# ---------------------------------------------------------------------------
# PoW：官方 WASM 在浏览器页面里求解
# ---------------------------------------------------------------------------

def fetch_pow_challenge(cred):
    headers = base_headers(cred)
    status, body = http_json("POST", "/api/v0/chat/create_pow_challenge", headers,
                             {"target_path": "/api/v0/chat/completion"})
    if status != 200:
        raise RuntimeError(f"create_pow_challenge 失败 {status}: {body[:200]!r}")
    return json.loads(body)["data"]["biz_data"]["challenge"]


def solve_pow(cred, challenge):
    """求解 DeepSeekHashV1 PoW，返回 x-ds-pow-response。

    优先用 Node 直接跑官方 WASM（无弹窗）；失败则降级到浏览器页面里求解。
    """
    answer = _solve_pow_node(challenge)
    if answer is None:
        answer = _solve_pow_browser(cred, challenge)
    return _make_pow_payload(challenge, answer)


def _make_pow_payload(challenge, answer):
    if answer is None:
        raise RuntimeError("PoW 求解失败")
    payload = {"algorithm": challenge["algorithm"],
               "challenge": challenge["challenge"],
               "salt": challenge["salt"],
               "answer": answer,
               "signature": challenge["signature"],
               "target_path": challenge["target_path"]}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw).decode("utf-8")


def _solve_pow_node(challenge):
    """Node 内置 WebAssembly 跑官方模块，零依赖、无授权弹窗。"""
    node = shutil.which("node")
    if not node:
        return None
    try:
        out = subprocess.run(
            [node, SOLVER_JS_PATH, WASM_PATH,
             challenge["challenge"],
             f"{challenge['salt']}_{challenge['expire_at']}_",
             str(challenge["difficulty"])],
            capture_output=True, text=True, timeout=120).stdout.strip()
        result = json.loads(out)
        return result.get("answer")
    except Exception:
        return None


def _solve_pow_browser(cred, challenge):
    """在浏览器页面里加载官方 DeepSeekHashV1 WASM 并求解。"""
    wasm_b64 = base64.b64encode(open(WASM_PATH, "rb").read()).decode()
    js = r"""
(async () => {
  const bin = atob(__WASM_B64__);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  const { instance } = await WebAssembly.instantiate(bytes, {});
  const e = instance.exports, mem = e.memory;
  const malloc = e.__wbindgen_export_0, stackPtr = e.__wbindgen_add_to_stack_pointer;
  const enc = new TextEncoder();
  const writeStr = (s) => {
    const b = enc.encode(s);
    const p = malloc(b.length, 1);
    new Uint8Array(mem.buffer, p, b.length).set(b);
    return [p, b.length];
  };
  const ret = stackPtr(-16);
  const [cp, cl] = writeStr(__CH__);
  const [pp, pl] = writeStr(__PREFIX__);
  e.wasm_solve(ret, cp, cl, pp, pl, __DIFF__);
  const dv = new DataView(mem.buffer);
  const status = dv.getInt32(ret, true);
  const answer = status === 0 ? null : Math.round(dv.getFloat64(ret + 8, true));
  stackPtr(16);
  if (answer === null) return JSON.stringify({ error: "solve_failed" });
  const payload = { algorithm: __ALG__, challenge: __CH__, salt: __SALT__,
                    answer, signature: __SIG__, target_path: __TP__ };
  return JSON.stringify({ answer, header: btoa(JSON.stringify(payload)) });
})()
"""
    js = (js
          .replace("__WASM_B64__", json.dumps(wasm_b64))
          .replace("__CH__", json.dumps(challenge["challenge"]))
          .replace("__PREFIX__", json.dumps(f"{challenge['salt']}_{challenge['expire_at']}_"))
          .replace("__DIFF__", json.dumps(challenge["difficulty"]))
          .replace("__ALG__", json.dumps(challenge["algorithm"]))
          .replace("__SALT__", json.dumps(challenge["salt"]))
          .replace("__SIG__", json.dumps(challenge["signature"]))
          .replace("__TP__", json.dumps(challenge["target_path"])))

    ep = cred["endpoint"]
    ws = bc.WebSocket(ep[2])
    cdp = bc.CDP(ws)
    target = cdp.call("Target.createTarget", {"url": f"https://{DOMAIN}/"})
    tid = target["targetId"]
    sid = cdp.call("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
    try:
        bc.wait_loaded(cdp, sid, DOMAIN, timeout=30)
        r = cdp.call("Runtime.evaluate",
                     {"expression": js, "awaitPromise": True, "returnByValue": True},
                     session_id=sid, timeout=120)
        result = r.get("result", {})
        if result.get("exceptionDetails"):
            raise RuntimeError("页面 JS 异常: " + json.dumps(result["exceptionDetails"])[:300])
        solved = json.loads(result["value"])
        if solved.get("error"):
            raise RuntimeError("WASM 求解失败: " + solved["error"])
        return solved["answer"]
    finally:
        try:
            cdp.call("Target.closeTarget", {"targetId": tid})
        except Exception:
            pass
        ws.close()


# ---------------------------------------------------------------------------
# 流式协议解析（CRDT patch + 裸文本块）
# ---------------------------------------------------------------------------

def parse_stream(text):
    """把 DeepSeek 的 CRDT 流重组为 fragment 列表（含 type/content）。"""
    fragments = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload:
            continue
        try:
            obj = json.loads(payload)
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        # 初始状态：v 里带 response.fragments
        v = obj.get("v")
        if isinstance(v, dict) and isinstance(v.get("response"), dict):
            fs = v["response"].get("fragments")
            if isinstance(fs, list):
                fragments = fs
            continue
        # 裸文本块：{"v": "..."} -> 追加到最后一个 fragment
        if isinstance(v, str) and "p" not in obj and "o" not in obj:
            if fragments:
                fragments[-1]["content"] = fragments[-1].get("content", "") + v
            continue
        o, p = obj.get("o"), obj.get("p") or ""
        if o == "APPEND" and p == "response/fragments/-1/content" and isinstance(v, str):
            if fragments:
                fragments[-1]["content"] = fragments[-1].get("content", "") + v
        elif o == "APPEND" and p == "response/fragments" and isinstance(v, list):
            fragments.extend(v)
        elif p == "response/fragments/-1/content" and o is None and isinstance(v, str):
            if fragments:
                fragments[-1]["content"] = fragments[-1].get("content", "") + v
    return fragments


def send_completion(cred, session_id, parent_message_id, prompt,
                    thinking=True, search=True, timeout=240):
    headers = base_headers(cred, referer=f"{BASE}/a/chat/s/{session_id}")
    headers["x-ds-pow-response"] = solve_pow(cred, fetch_pow_challenge(cred))
    body = {
        "chat_session_id": session_id,
        "parent_message_id": parent_message_id,
        "prompt": prompt,
        "ref_file_ids": [],
        "thinking_enabled": thinking,
        "search_enabled": search,
        "action": None,
        "preempt": False,
    }
    if parent_message_id is None:
        body["model_type"] = "default"  # 新线程必须选模型；续聊沿用原线程模型
    status, resp = http_json("POST", "/api/v0/chat/completion", headers, body, timeout=timeout)
    if status != 200:
        raise RuntimeError(f"completion 失败 {status}: {resp[:300]!r}")
    return parse_stream(resp.decode("utf-8", "replace"))


def create_session(cred):
    status, body = http_json("POST", "/api/v0/chat_session/create", base_headers(cred), {})
    if status != 200:
        raise RuntimeError(f"创建会话失败 {status}: {body[:200]!r}")
    return json.loads(body)["data"]["biz_data"]["chat_session"]["id"]


def fetch_history(cred, session_id):
    status, body = http_json("GET", f"/api/v0/chat/history_messages?chat_session_id={session_id}",
                             base_headers(cred))
    if status != 200:
        raise RuntimeError(f"history_messages 失败 {status}: {body[:200]!r}")
    return json.loads(body)["data"]["biz_data"]["chat_messages"]


def fragment_text(msg):
    parts = []
    for fr in msg.get("fragments") or []:
        if isinstance(fr, dict) and fr.get("content"):
            parts.append((fr.get("type"), fr["content"]))
    return parts


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="通过 CDP 复用浏览器登录态调用 DeepSeek Chat（纯标准库）")
    ap.add_argument("--new", action="store_true", help="创建新会话")
    ap.add_argument("--session-id", default=None, help="chat_session_id")
    ap.add_argument("--parent-message-id", type=int, default=None,
                    help="续聊时用最后一条消息的 id")
    ap.add_argument("--prompt", default=None, help="要发送的内容")
    ap.add_argument("--history", action="store_true", help="打印会话历史")
    ap.add_argument("--no-thinking", action="store_true", help="关闭思考模式")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    args = ap.parse_args(argv)

    if args.history:
        if not args.session_id:
            raise SystemExit("--history 需要 --session-id")
        cred = get_credentials()
        msgs = fetch_history(cred, args.session_id)
        out = []
        for m in msgs:
            out.append({"message_id": m.get("message_id"), "role": m.get("role"),
                        "status": m.get("status"), "fragments": fragment_text(m)})
        print(json.dumps(out, ensure_ascii=False, indent=2) if args.json
              else json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if not args.prompt:
        raise SystemExit("需要 --prompt（或 --history）")

    cred = get_credentials()
    if args.new:
        session_id = create_session(cred)
        parent_id = None
        print(f"[ok] 新会话: {session_id}")
    else:
        if not args.session_id:
            raise SystemExit("需要 --session-id 或 --new")
        session_id = args.session_id
        parent_id = args.parent_message_id

    fragments = send_completion(cred, session_id, parent_id, args.prompt,
                                thinking=not args.no_thinking)
    result = {"session_id": session_id, "fragments": fragments}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for fr in fragments:
            if not isinstance(fr, dict) or not fr.get("content"):
                continue
            ftype = fr.get("type")
            if ftype == "THINK":
                print(f"[思考 {len(fr['content'])} 字，已省略]")
            else:
                print(f"[{ftype or 'RESPONSE'}]\n{fr['content']}\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)
