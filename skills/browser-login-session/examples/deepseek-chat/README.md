# 示例：DeepSeek Chat（原始输入 → 成品）

## 目标

用浏览器已登录身份调用 `chat.deepseek.com` 的私有流式接口，验证
`browser-login-session` 的完整模式：**CDP 取登录态 → 求解 PoW → 流式调用 → 重组响应**。

## 设计：请求字段的来源

| 请求字段 | 来源 |
| --- | --- |
| Cookie（`ds_session_id` 等） | CDP `Network.getCookies` |
| `authorization: Bearer` | localStorage `userToken` |
| `x-hif-dliq` / `x-hif-leim` | localStorage 缓存值 |
| `x-ds-pow-response` | 每次现算：Node 跑官方 WASM（`pow_solve.mjs`） |
| UA / sec-ch-ua | CDP `Runtime.evaluate` |

## 成品

`examples/deepseek-chat/deepseek_chat.py`：

```bash
cd skills/browser-login-session/examples/deepseek-chat
python3 deepseek_chat.py --new --prompt "你好"
python3 deepseek_chat.py --session-id <id> --parent-message-id <id> --prompt "续聊"
```

## 本目录文件

| 文件 | 用途 |
| --- | --- |
| `deepseek_chat.py` | 可运行示例脚本（依赖核心实现 `scripts/browser_cdp.py`） |
| `pow_solve.mjs` / `sha3_wasm_bg.wasm` | PoW 求解所需资源（Node 内置 WebAssembly） |
| `raw-request.md` | 原始输入：浏览器抓包骨架 |
| `deepseek-protocol.md` | 协议细节：PoW、续聊语义、CRDT 流格式 |
| `README.md` | 本文件：设计总结 |

## 复盘要点

- PoW 一次性：复用旧值返回 `INVALID_POW_RESPONSE`；
- 流协议是 CRDT patch（`{"p":...,"o":"APPEND","v":...}` + 裸 `{"v":...}` 文本块），
  不是老的 `type:delta`，必须按 fragment（THINK/RESPONSE）重组；
- 续聊必须传 `parent_message_id`（线程最后一条消息 id），否则模型丢失上下文。

协议细节见本目录的 `deepseek-protocol.md`。
