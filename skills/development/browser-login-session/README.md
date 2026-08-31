# browser-login-session

无感复用浏览器已登录态：通过 CDP 从本机 Chrome/Edge 提取指定域名的登录凭据，
组装为 API 请求头。纯 Python 标准库，零 pip 依赖，零浏览器驱动。

## 快速开始

```bash
cd scripts

# 一次性配置（复制登录态到专用 profile）
python3 browser_cdp.py github.com --setup

# 日常取 Cookie + localStorage
python3 browser_cdp.py github.com --with-extra --json
```

## 文档

- [SKILL.md](SKILL.md) — 技能说明、工作流与安全规范
- [docs/architecture.md](docs/architecture.md) — 架构决策：为什么 CDP + 专用 profile
- [docs/endpoint-matrix.md](docs/endpoint-matrix.md) — Chrome 版本间的端点发现行为
- [docs/security.md](docs/security.md) — 安全模型与使用边界
- [docs/deepseek-example.md](docs/deepseek-example.md) — DeepSeek 端到端示例协议

## 一句话提醒

登录态等同口令：只取用户明确指定的域名，不打印、不落盘、不进日志；
调试端口用完即关（`--close-browser`）。
