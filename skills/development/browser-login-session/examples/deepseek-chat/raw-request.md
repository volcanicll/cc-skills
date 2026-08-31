# 原始输入：DeepSeek 流式接口抓包（字段已脱敏）

浏览器 DevTools 抓到的 `POST /api/v0/chat/completion` 请求骨架：

```bash
curl --url 'https://chat.deepseek.com/api/v0/chat/completion' \
  -H 'accept: */*' \
  -H 'authorization: Bearer <userToken，来自 localStorage>' \
  -H 'content-type: application/json' \
  -b '<cookieHeader，来自 CDP>' \
  -H 'origin: https://chat.deepseek.com' \
  -H 'referer: https://chat.deepseek.com/a/chat/s/<chat_session_id>' \
  -H 'sec-ch-ua: "Chromium";v="152", ...' \
  -H 'user-agent: <浏览器 UA>' \
  -H 'x-client-version: 2.4.0' \
  -H 'x-hif-dliq: <localStorage hif_dliq_cached>' \
  -H 'x-hif-leim: <localStorage hif_leim_cached>' \
  -H 'x-ds-pow-response: <每次现算，不能复用>' \
  --data-raw '{"chat_session_id":"<id>","parent_message_id":null,"model_type":"default","prompt":"...","ref_file_ids":[],"thinking_enabled":true,"search_enabled":true,"action":null,"preempt":false}'
```

要点：Authorization / hif 头来自 localStorage；Cookie 来自 CDP；
`x-ds-pow-response` 每次请求现算（复用旧值会得到 `INVALID_POW_RESPONSE`）。
