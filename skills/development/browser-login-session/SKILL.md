---
name: browser-login-session
description: 无感复用浏览器已登录态，通过 CDP 从本机 Chrome/Edge 提取指定域名的登录凭据（Cookie、Authorization Token、localStorage）并组装为 API 请求头。纯 Python 标准库、零 pip 依赖，不碰磁盘 Cookie 加密、不注入页面、不绕过验证码与风控。同时作为本仓库创建新 skill 的元 skill 模板。Use when users ask 复用浏览器登录态、获取已登录站点 Cookie/Token、用当前登录身份调 API、无感调用需登录接口、browser login session、CDP cookies.
metadata:
  triggers:
    - 复用浏览器登录态
    - 获取已登录站点 Cookie/Token
    - 用当前登录身份调 API
    - 无感调用需登录接口
    - CDP cookies
    - 浏览器会话凭据
---

# Browser Login Session

无感复用本机浏览器已登录态：通过 CDP 提取指定域名的 Cookie 与 localStorage 凭据，
组装为可直接调用的 API 请求头。核心脚本为纯 Python 标准库，零第三方依赖。

本目录同时是仓库的**元 skill**：创建新 skill 时以此目录结构为模板，
步骤见 `references/skill-authoring.md`。

## 能力边界

- 可以：读指定域名 Cookie（含 HttpOnly）与 localStorage/sessionStorage
  （token、CSRF、自定义请求头）；组装请求头；`--resync` 同步登录态。
- 不做：读磁盘 Cookie 数据库 / 解密 App-Bound、Keychain；注入页面或操作 UI；
  绕过验证码、人机校验与风控；枚举用户未指定域名。

## 快速开始

```bash
cd scripts

# 一次性：复制日常浏览器登录态到专用 profile（约 10 秒）
python3 browser_cdp.py github.com --setup

# 日常：Cookie + UA + localStorage 结构化输出
python3 browser_cdp.py github.com --with-extra --json
```

设计原理（为什么 CDP + 专用 profile）：`references/architecture.md`；
Chrome 版本间的端点行为：`references/endpoint-matrix.md`。

## Agent 工作流

1. 目标域名来自用户明确请求（登录态是敏感数据）；
2. 首次 `--setup`，之后直接取数据；
3. 取 `cookieHeader` 与 `extra.localStorage` 中的 token/自定义头组装请求；
4. 401/403 → 提示重新登录或 `--resync`，不静默重试；
5. 输出不回显完整凭据。

## 红线（完整安全模型见 references/security.md）

- 只取用户明确指定域名，绝不导出全量 Cookie；
- 不回显、不落盘、不进日志；用完 `--close-browser`；
- 不绕过验证码/风控；分发前提示 ToS 边界。

## 验证

```bash
python3 tests/test_cdp_websocket.py   # mock CDP 端到端测试（纯标准库）
```

## 示例

`examples/deepseek-chat/`：从浏览器抓包到流式 API 调用的完整走查
（脚本在 `scripts/deepseek_chat.py`，协议细节见 `references/deepseek-protocol.md`）。

## 目录结构

```
browser-login-session/        # 元 skill 模板
├── SKILL.md                  # 精简入口（本文件）
├── manifest.json             # 元数据：名称/版本/依赖/结构
├── references/               # 详细指引（按需增删）
│   ├── architecture.md       # 架构决策
│   ├── endpoint-matrix.md    # 端点发现矩阵（实测）
│   ├── security.md           # 安全模型
│   ├── deepseek-protocol.md  # DeepSeek 协议参考
│   └── skill-authoring.md    # 元 skill：新 skill 创建清单
├── scripts/                  # 核心脚本（零第三方依赖）
├── examples/                 # 原始输入 → 设计总结 → 用法
└── tests/                    # 可运行验证
```
