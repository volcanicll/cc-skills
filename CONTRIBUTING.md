# 贡献指南

本仓库是一个个人 Claude Agent Skills 集合，包含目录结构、规范与自动化基础设施，方便持续扩展新 skill。

## 仓库结构

```
cc-skills/
├── .claude-plugin/
│   └── marketplace.json      # 插件市场配置（由脚本生成，勿手改）
├── skills/                   # Skill 目录（一级扁平组织）
│   ├── browser-login-session/
│   ├── changelog-writer/
│   ├── eli5/
│   └── ...
├── scripts/
│   └── sync_marketplace.py   # 同步/校验 marketplace 的脚本
├── AGENTS.md                 # 项目协作规范（含技能开发规范）
├── CONTRIBUTING.md           # 本文档
└── README.md                 # 仓库说明与安装指引
```

## Skill 规范

### 目录结构

每个 skill 位于 `skills/<skill-name>/`（一级目录存放，不再按分类建子目录）：

- `<skill-name>`：英文短横线命名（kebab-case）

新 skill 以 `skills/browser-login-session/` 为元 skill 模板，推荐结构：

```
skill-name/
├── SKILL.md           # 精简入口：能力边界、快速开始、工作流、红线
├── manifest.json      # 元数据（名称/版本/依赖/结构）
├── references/        # 详细指引（架构、协议、安全等，按需增减）
├── scripts/           # 核心可执行脚本（优先零第三方依赖）
├── examples/          # 原始输入 → 设计总结 → 用法示例
└── tests/             # 可运行的验证脚本
```

创建清单见 `browser-login-session/references/skill-authoring.md`。

### SKILL.md frontmatter

`SKILL.md` 必须包含合法的 YAML frontmatter：

```markdown
---
name: my-skill-name
description: 说明该 skill 的用途与触发场景，描述应具体、可触发
metadata:
  category: development
---

# 标题

正文指令...
```

要求（符合 VS Code skills 标准规范，顶层属性仅支持 `name`、`description`、`metadata` 等）：

- `name` 必填，且必须与 skill 目录名完全一致
- `description` 必填，说明「做什么」与「何时使用」，建议包含触发关键词
- `metadata.category` 必填，所属分类（`creative`、`development`、`learning`、`meta` 之一，置于 `metadata` 下以兼容 VS Code skills schema）
- 可选的 `metadata.triggers` 用于补充触发词

## 基础设施

### Marketplace 同步

`.claude-plugin/marketplace.json` 由 `scripts/sync_marketplace.py` 自动生成，根据各技能 frontmatter 的 `metadata.category` 自动归类生成插件（`<category>-tools`），**禁止手动编辑**。

常用命令：

```bash
# 重新生成 marketplace.json
python3 scripts/sync_marketplace.py

# 仅校验，不写入（提交前/CI 使用）
python3 scripts/sync_marketplace.py --check

# 查看扫描到的 skill 列表
python3 scripts/sync_marketplace.py --verbose
```

### skills CLI 支持

本仓库的一级扁平目录结构（`skills/<skill-name>/`）全面兼容开放标准的 [Agent Skills CLI](https://skills.sh)（`npx skills add volcanicll/cc-skills [--skill <name>]`），可直接被 Claude Code、Cursor、GitHub Copilot、Cline 等 18+ 种主流 AI Agent 识别与安装。

## 新增 skill 流程

1. 以元 skill `skills/browser-login-session/` 为模板复制骨架
2. 创建 `skills/<skill-name>/SKILL.md`，frontmatter 含合法的 `name`、`description` 与 `metadata.category`
3. 按 `references/skill-authoring.md` 清单补充 manifest / references / scripts / examples / tests
4. 运行 `python3 scripts/sync_marketplace.py` 同步 marketplace
5. 更新 `README.md`：
   - 在对应分类的技能表格中新增一行（中文描述）
   - 更新「Repository Structure」结构图
   - 如需要，补充「Usage」触发示例
6. 同步 `docs/index.html` 落地页：技能总数、分类计数、技能列表与描述
7. 运行 `python3 scripts/sync_marketplace.py --check` 确认校验通过
8. 运行 skill 自带测试（如有 `tests/`）并确认无密钥残留
9. 遵循 `AGENTS.md` 的 Git 提交规范提交：
   ```
   feat(skills): add xxx skill
   ```

## 校验清单

提交前确认：

- [ ] SKILL.md frontmatter 合法（`name` 与目录名一致、`description` 非空）
- [ ] 结构遵循元 skill 模板（SKILL.md + manifest.json + references/ + scripts/ + examples/ + tests/ 按需）
- [ ] 自带测试通过、无密钥残留
- [ ] `python3 scripts/sync_marketplace.py --check` 通过
- [ ] README 技能表格与结构图已更新
- [ ] `docs/index.html` 落地页已同步（技能总数/分类计数/描述）
- [ ] 提交信息符合 `<type>(<scope>): <description>` 格式
- [ ] 无调试代码与无关文件
