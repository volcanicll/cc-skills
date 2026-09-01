# 架构与零依赖设计

## 目标

在保持现有功能（统计 → 生成 Excel → 导入 → 导出 → 状态流转）不变的前提下，
把用户额外依赖降到 **零**：不再需要 `pip install` 任何第三方包，
只依赖 Python 3.9+ 标准库 + 本机 Chrome/Edge + git。

## 模块与依赖映射

| 原第三方依赖 | 用途 | 替代实现 | 模块 |
| --- | --- | --- | --- |
| `websocket-client` | CDP WebSocket 提取登录态 | 手写 RFC 6455 客户端（移植自 browser-login-session） | `scripts/rdc/ws.py` |
| `requests` | 平台接口调用 | `urllib.request`（JSON / multipart / 下载） | `scripts/rdc/net.py` |
| `pyyaml` | 配置解析 | 内置 YAML 子集解析器 | `scripts/rdc/yamlio.py` |
| `openpyxl` | Excel 生成/读取 | `zipfile` + 手写 XML 最小 xlsx 读写 | `scripts/rdc/xlsx.py` |

## 关键实现要点

### WebSocket（ws.py）
- 手写 RFC 6455 客户端：`socket` 建连、`base64`/`hashlib` 计算
  `Sec-WebSocket-Accept`、客户端帧掩码、自动应答 ping。
- **不发送 Origin 头**（等价原 `suppress_origin=True`），规避 Chrome/Edge CDP
  对带 Origin 连接的 403 拒绝。
- `CDP.call(method, params, session_id)` 负责 id 配对与事件过滤。

### HTTP（net.py）
- `request_json(method, url, headers, payload)`：JSON 请求（GET/POST/PUT）。
- `post_multipart(url, headers, fields, files)`：手拼 multipart/form-data
  （boundary + Content-Length），用于 `check-excel` / `importExcel`。
- `get_bytes(url, headers)`：文件下载（导出 fileUrl、错误报告）。
- 非 2xx 抛 `HttpError`；非 JSON 响应抛错并截断展示。

### YAML（yamlio.py）
- 行级递归解析，支持本项目配置子集：缩进 mapping、块状 sequence、
  单/双引号字符串、数字/布尔/null、行注释与行尾注释（引号内 `#` 不处理）。
- 复杂配置可改用 `rdc-config.json`（`load_config` 原生支持）。

### Excel（xlsx.py）
- **写入**：最小 OOXML 包（`[Content_Types]` / rels / workbook / sheet /
  styles），inlineStr 单元格 + 表头样式（宋体加粗灰底、细边框、自动换行）。
- **读取**：支持 sharedStrings（含富文本 run 拼接）、inlineStr、`str`、
  number、boolean；取首个工作表为二维表 `(headers, rows)`。
- 生成与读取均不依赖 openpyxl，覆盖平台导出文件与本地生成文件。

## 数据流

```
stats(本机 git) → commits.json → work_items.json(AI 分组)
      → build-excel → 工作量.xlsx → prepare(清编号/状态) → validate → import
      → 从 import 响应提取工作项编号 → updateWorkItems/edit 接口逐级流转
```

## 状态流转（不再走 Excel 导入）

- 创建：`importExcel` 导入响应 `bo.taskInfo.succeededItems[].data["1"]`
  返回工作项编号（如 `P22CQQYYF0016-6864`）。
- 流转：`PUT {wic_base_url}/api/workspaces/{workspace}/work_items/updateWorkItems/edit`
  ，body 为 `workItems[] + fields[]`（`System_State`，`modifyType: replace`），
  逐级按 `status_flow` 调用，跳级由平台报"工作流不存在"。
- 优点：无需每级导出/导入 Excel，更快且不产生中间文件；编号来源于导入响应，
  无需人工维护。

## 安全

- `auth.json` 含登录态 cookie / token，禁止提交（`.gitignore` 已覆盖）。
- 输出不回显完整凭据；仅打印员工号/项目/团队等摘要。
