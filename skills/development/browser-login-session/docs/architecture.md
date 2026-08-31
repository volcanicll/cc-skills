# 架构与决策记录

## 目标

在 API 层级无感复用浏览器已登录态：以“当前浏览器登录身份”调用需要登录的私有接口，
同时把用户额外环境配置压到最小。

## 为什么是 CDP，而不是磁盘解密

最初的设计是从操作系统本地直接提取已解密的 Cookie 数据库（macOS Keychain /
Windows DPAPI + AES），该路线在 2026 年已被平台逐步封死：

| 平台/版本 | 磁盘解密现状 | CDP 方案 |
| --- | --- | --- |
| Windows Chrome/Edge 127+ | App-Bound Encryption：普通进程 DPAPI 解不了主密钥 | 浏览器自行解密，无影响 |
| Windows Chrome/Edge 140+ | 所有 Cookie 默认 v20 + ABE，磁盘方案彻底失效 | 无影响 |
| macOS | 首次读 Keychain 必弹授权框，无头环境卡死 | 浏览器内已解密 |
| Linux | 主密钥硬编码可解，但多用户容器有泄露风险 | 浏览器内已解密 |

CDP 的核心优势：**加解密全部由浏览器自己完成**，工具只从调试协议拿解密后的明文，
天然免疫 App-Bound / Keychain / WAL 锁 / Schema 演进等所有磁盘侧问题。

## 为什么是“专用 profile”

Chrome 136+ 出于安全原因，**静默忽略对默认用户数据目录开远程调试端口的参数**。
Chrome ≥144 的 `chrome://inspect` 开关虽然能用默认 profile，但实测**每次新连接都要
人工点一次“允许”**，授权不跨连接复用，无法无人值守。

因此唯一满足“无感 + 零配置”的组合是：

1. **一次性复制登录态**（`--setup`）：把日常 profile 的 `Local State` + 目标
   profile 目录复制到 `~/.browser_cdp/<browser>`，跳过 Cache 等大目录；
2. **专用实例常驻调试端口**（默认 9333）：同一个 `--user-data-dir` 只能有一个
   浏览器进程，日常浏览器用默认目录，两者互不冲突；
3. 之后每次运行：探测端点 → 连接浏览器级 WebSocket → 取 Cookie / localStorage。

登录态在专用 profile 里**跨重启保持**（Cookie 数据库与密钥都在复制结果里），
日常浏览器重新登录后执行 `--resync` 重新同步一次即可。

## 数据流

```
用户触发 skill
   │
   ▼
[1] 端点发现：显式 --port → 专用目录 → 真实目录
   │
   ▼
[2] 连接浏览器级 WebSocket（手写 RFC 6455 客户端，标准库）
   │
   ▼
[3] Target.createTarget(url) + attachToTarget(flatten)
   │
   ▼
[4] Network.getCookies(urls)        → Cookie（含 HttpOnly）
    Runtime.evaluate(localStorage)  → Token / 自定义头
   │
   ▼
[5] 组装 Cookie 头 + UA/指纹头 → 调用目标 API
```

## 端点发现优先级

1. 显式 `--port`：HTTP 探测 `/json/version`；
2. 专用目录：`DevToolsActivePort` 文件（auto-connect 模式）或 HTTP 探测；
3. 真实目录：同上（用于兼容用户已开启 auto-connect 的情况）。

详细行为矩阵见 [endpoint-matrix.md](endpoint-matrix.md)。

## 登录态生命周期

- 专用 profile 是日常 profile 的**快照**，不是实时镜像；
- 日常浏览器换号 / 重新登录 / 会话过期后，`--resync` 重新同步；
- API 返回 401/403 时优先提示用户，而不是静默重试。

## 已知限制与降级阶梯

- 反爬严格的站点会校验 TLS 指纹、请求头顺序、CSRF token：光有 Cookie 可能仍被拦；
- 设备绑定会话（Google DBSC、Microsoft 条件访问）无法跨进程重放，任何方案都救不了；
- 因此建议保留降级阶梯：**磁盘提取（best-effort）→ CDP（本 skill 默认）→
  手动粘贴 Cookie 头（兜底）**，并明确“零配置”与“高保真”不可兼得。

## 版本风险

Chrome 每 4 周一个大版本，端点发现行为可能变化（本 skill 的矩阵基于 2026-08
Chrome 151 实测）。新增版本若出现“端口在但连不上”，优先检查
`DevToolsActivePort` 文件与 `/json/version` 的组合行为，见 endpoint-matrix。
