# 元 Skill：新 Skill 创建指南

本仓库的 `browser-login-session` 是新建 skill 的结构模板（元 skill）。
创建新 skill 时复制本目录骨架，按以下清单裁剪。

## 标准结构

| 目录/文件 | 用途 | 何时需要 |
| --- | --- | --- |
| `SKILL.md` | 精简入口：能力边界、快速开始、工作流、红线 | 必填 |
| `manifest.json` | 元数据：名称、版本、依赖、结构说明 | 推荐 |
| `references/` | 详细指引：架构、协议、安全等 | 有实现细节时 |
| `scripts/` | 可执行核心代码 | 有逻辑时 |
| `examples/` | 原始输入 → 设计总结 → 用法示例 | 有端到端用例时 |
| `tests/` | 可运行的验证脚本（纯标准库优先） | 有可测逻辑时 |

## SKILL.md 写作原则

- frontmatter：`name` 与目录名一致；`description` 写「做什么 + 何时触发」并含触发词；
- 正文保持精简：入口只放边界 / 快速开始 / 工作流 / 红线，细节下沉到 `references/`；
- 红线单独成节：涉及敏感数据、破坏性操作、外部副作用的内容必须写明。

## 创建步骤清单

1. 从本目录复制骨架（SKILL.md + manifest.json + references/ + tests/）；
2. 起名：英文 kebab-case，如 `pdf-table-extractor`；
3. 先写 `description`（触发路由靠它），再补正文；
4. 核心逻辑放 `scripts/`，优先纯标准库 / 系统自带工具，避免第三方依赖；
5. 细节文档放 `references/`，每个文件只讲一件事；
6. 端到端用例放 `examples/<name>/`：`raw-input.*`（原始输入）+ `README.md`（设计总结与用法）；
7. 可测逻辑放 `tests/`，脚本可直接运行（`python3 tests/test_xxx.py`）；
8. 敏感信息扫描：提交前 `rg` 检查无密钥 / Token；
9. 按仓库规范同步 marketplace 并更新根 README；
10. 小步提交，遵循 AGENTS.md 的 conventional commit 规范。

## 质量门禁

- `python3 scripts/sync_marketplace.py --check` 通过；
- 脚本可运行（py_compile / 测试通过）；
- 无密钥、无调试残留、无与主题无关的文件。
