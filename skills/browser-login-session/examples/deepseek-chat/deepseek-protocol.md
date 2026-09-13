# 示例：DeepSeek Chat（deepseek_chat.py）

本示例演示完整模式：**CDP 取登录态 → 求解 PoW → 流式调用私有 API → 重组响应**。
它是 `browser_cdp.py` 能力的端到端用例，也是“登录态获取”之外的配套样板。

## 为什么需要它

DeepSeek 网页版（`chat.deepseek.com`）的 `/api/v0/chat/completion` 是私有接口，
要求：

- `Cookie`（`ds_session_id` 等，HttpOnly）；
- `authorization: Bearer <token>`（存在 localStorage 的 `userToken`）；
- `x-hif-dliq` / `x-hif-leim`（localStorage 缓存值）；
- `x-ds-pow-response`：每次请求都要现算的 Proof-of-Work（**不能复用**，
  复用会得到 `INVALID_POW_RESPONSE`）。

## 链路

```bash
cd skills/browser-login-session/examples/deepseek-chat
python3 deepseek_chat.py --new --prompt "你好"
```

1. `get_credentials()`：CDP 取 Cookie + localStorage（Bearer / hif 头）；
2. `POST /api/v0/chat/create_pow_challenge`：拿 challenge（salt / expire_at /
   difficulty=144000 / challenge 哈希 / signature）；
3. `solve_pow()`：求解 `DeepSeekHashV1`——
   - 首选 `pow_solve.mjs`：Node 内置 WebAssembly 直接跑官方
     `sha3_wasm_bg.wasm`（零 npm 依赖，实测约 0.05s）；
   - 降级：在浏览器页面里实例化同一份 WASM（依赖调试连接可用）；
4. `POST /api/v0/chat/completion`：流式 SSE；
5. `parse_stream()`：按 CRDT patch 协议重组 fragment（THINK / RESPONSE）。

## 流式协议（2026 实测）

不是老的 `{"type":"delta","text":...}`，而是：

```
event: ready
data: {"request_message_id":5,"response_message_id":6,...}

data: {"v":{"response":{"fragments":[...]}}}          # 初始状态
data: {"p":"response/fragments/-1/content","o":"APPEND","v":"."}   # 显式追加
data: {"v":" "}                                        # 裸文本块，追加到最后一个 fragment
data: {"p":"response/fragments","o":"APPEND","v":[{...}]}          # 新增 fragment
data: {"p":"response/status","o":"SET","v":"FINISHED"}
event: close
```

fragment 类型：`THINK`（思考）、`RESPONSE`（回答）、`TIP`（AI 生成提示）、`REQUEST`。

## 续聊语义（重要）

- 新线程：`parent_message_id: null` + `model_type: "default"`；
- 续聊：`parent_message_id` 填**线程最后一条消息的 id**，且**不要再传
  `model_type`**（沿用原线程模型）；
- 如果 `parent_message_id` 传 `null`，服务器会把它当成新的根消息，**丢掉线程
  上下文**——表现为模型“看不到”之前的对话内容；
- 查历史：`GET /api/v0/chat/history_messages?chat_session_id=<id>`，
  内容在每条消息的 `fragments` 里。

## 常见问题

| 现象 | 原因与处理 |
| --- | --- |
| `INVALID_POW_RESPONSE` | PoW 一次性 / 已过期，重新运行脚本（自动现算） |
| WS 握手挂起 | 浏览器处于 auto-connect 模式，需在浏览器里点“允许”；或改用 `--setup` 专用 profile |
| 响应是 JSON 而不是流 | 请求头不对（如缺 hif / 旧 UA），先对照 `base_headers()` |
| 模型“看不到”之前的对话 | `parent_message_id` 传了 null，用历史里最后一条消息 id |
| 直接 curl 首页被 Rate Limit | WAF 对无浏览器指纹的请求限流，走本脚本的完整请求头 |

## 复用模式

把 `deepseek_chat.py` 当作模板：把 `DOMAIN`、凭据字段名、目标 API 路径换掉，
即可用同一套 CDP 登录态逻辑接入其他“浏览器登录后才能调”的站点。
