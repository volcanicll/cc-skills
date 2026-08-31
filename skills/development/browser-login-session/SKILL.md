---
name: browser-login-session
description: 无感复用浏览器已登录态，通过 CDP 从本机 Chrome/Edge 提取指定域名的登录凭据（Cookie、Authorization Token、localStorage 等）并组装为 API 请求头。适用于以当前浏览器登录身份调用需登录的私有接口、抓取登录后数据、自动化测试等场景。纯 Python 标准库实现，零 pip 依赖，不碰磁盘 Cookie 加密，不注入页面，不绕过验证码与风控。Use when users ask 复用浏览器登录态、获取已登录站点 Cookie/Token、用当前登录身份调用 API、无感调用需登录接口、browser login session、CDP cookies、读取浏览器会话凭据.
metadata:
  triggers:
    - 复用浏览器登录态
    - 获取已登录站点的 Cookie
    - 用当前登录身份调 API
    - 无感调用需登录接口
    - CDP cookies
    - browser login session
    - 读取浏览器会话凭据
---

# 浏览器登录态复用（Browser Login Session）

通过 CDP（Chrome DevTools Protocol）获取本机浏览器**已登录站点**的会话凭据，
组装成可直接用于 API 调用的请求头。核心设计目标是**最小化用户环境配置**：
纯 Python 标准库、零 pip 依赖、无浏览器驱动、无编译步骤。

## 能力边界

可以：

- 读取指定域名的 Cookie（含 HttpOnly）与 localStorage / sessionStorage
  （Authorization Token、CSRF、hif 等自定义请求头来源通常在这里）；
- 组装 `Cookie` 头与 UA / client hints 等指纹头，供后续 API 调用；
- 浏览器重新登录后通过 `--resync` 同步登录态。

明确不做：

- **不读磁盘 Cookies 数据库**，不解密 App-Bound / Keychain（加解密全部由浏览器完成）；
- 不注入页面、不操作 UI、不自动化点击；
- 不绕过验证码 / 人机校验 / 站点风控；
- 不改写浏览器数据，不枚举用户未指定的域名。

## 前置条件

- Python >= 3.8（仅标准库）；
- 本机已安装 Chrome 或 Edge，且目标站点已登录；
- 可选 Node：仅 DeepSeek 示例的 PoW 求解需要（无 Node 时自动降级到浏览器内求解）。

## 快速开始

```bash
cd skills/development/browser-login-session/scripts

# 一次性配置：复制日常浏览器登录态到专用 profile 并启动调试实例（约 10 秒）
python3 browser_cdp.py github.com --setup

# 日常：取 Cookie 头
python3 browser_cdp.py github.com

# 结构化输出（Agent 消费推荐）
python3 browser_cdp.py github.com --json

# 额外读 UA / localStorage / sessionStorage（token 等常在这里）
python3 browser_cdp.py github.com --with-extra --json
```

`--setup` 会优雅退出日常浏览器几秒以复制登录态（请先提醒用户保存工作）；
此后每次运行直接连接专用实例，**无弹窗、无交互、可无人值守**。

## Agent 工作流

1. **确认意图与域名**：登录态是敏感数据，目标域名必须来自用户的明确请求。
2. **首次使用**：先执行 `--setup`（一次性）；日常运行直接取数据。
3. **取数据**：
   ```bash
   python3 browser_cdp.py <domain> --with-extra --json
   ```
4. **组装请求**：从 JSON 提取 `cookieHeader`，从 `extra.localStorage` 提取
   token / 自定义头（如 DeepSeek 的 `userToken`、`hif_dliq_cached`）。
5. **调用目标 API**：若返回 401/403，提示用户重新登录或执行 `--resync`，
   不要静默无限重试。
6. **输出纪律**：不要把完整 Cookie / Token 明文回显到对话或日志。

## 安全规范（必须遵守）

- 凭据等同口令：只在用户明确要求时获取；不打印、不落盘、不进日志；
- 只读取用户指定域名，绝不导出全部 Cookie；
- 浏览器重启只发生在用户可感知的 `--setup` / `--resync`；日常运行不碰日常浏览器；
- 调试端口对本机所有进程开放，等同可读全部 Cookie：
  任务结束用 `--close-browser` 关闭专用实例，不要长期挂起调试端口；
- 不绕过验证码、不模拟人机校验、不绕过目标站点风控；
- 目标站点 ToS 可能禁止自动复用会话，使用前提醒用户确认用途边界。

详细威胁模型见 `docs/security.md`。

## 故障排查速查

| 现象 | 处理 |
| --- | --- |
| `未找到 CDP 端点` | 先 `--setup`；或浏览器处于 auto-connect 模式时需在 `chrome://inspect/#remote-debugging` 里点一次“允许” |
| Windows Chrome/Edge 140+ | 磁盘解密已失效，本 skill 走 CDP 无此问题 |
| `INVALID_POW_RESPONSE`（DeepSeek 示例） | PoW 一次性，脚本会自动现算，勿手动复用旧值 |
| 401/403 | 登录态过期：浏览器重新登录后 `--resync` |

端点在 Chrome 版本间的行为差异见 `docs/endpoint-matrix.md`。

## 示例：DeepSeek Chat

`scripts/deepseek_chat.py` 演示完整模式：CDP 取凭据 → PoW 求解（Node 跑官方
WASM）→ 流式 API → CRDT 协议重组：

```bash
python3 deepseek_chat.py --new --prompt "你好"
python3 deepseek_chat.py --session-id <id> --parent-message-id <id> --prompt "续聊"
python3 deepseek_chat.py --session-id <id> --history
```

协议细节见 `docs/deepseek-example.md`。

## 文件结构

```
browser-login-session/
├── SKILL.md                   # 本文件：技能说明与工作流
├── README.md                  # 独立速查入口
├── scripts/
│   ├── browser_cdp.py         # 核心：CDP 登录态提取（纯标准库）
│   ├── deepseek_chat.py       # 示例：DeepSeek 流式 API 调用
│   ├── pow_solve.mjs          # 示例：DeepSeekHashV1 PoW 求解（Node 内置 WebAssembly）
│   └── sha3_wasm_bg.wasm      # 示例：DeepSeek 官方 PoW 模块
└── docs/
    ├── architecture.md        # 架构决策（为什么 CDP + 专用 profile）
    ├── endpoint-matrix.md     # 端点发现模式矩阵（版本实测）
    ├── security.md            # 安全模型与使用规范
    └── deepseek-example.md    # DeepSeek 示例协议详解
```
