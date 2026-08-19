# 贡献指南

本仓库是一个个人 Claude Agent Skills 集合，包含目录结构、规范与自动化基础设施，方便持续扩展新 skill。

## 仓库结构

```
cc-skills/
├── .claude-plugin/
│   └── marketplace.json      # 插件市场配置（由脚本生成，勿手改）
├── skills/                   # Skill 目录（按分类组织）
│   ├── creative/             # 创意设计
│   ├── development/          # 开发工具
│   ├── learning/             # 学习教育
│   └── meta/                 # 元工具
├── scripts/
│   └── sync_marketplace.py   # 同步/校验 marketplace 的脚本
├── AGENTS.md                 # 项目协作规范（含技能开发规范）
├── CONTRIBUTING.md           # 本文档
└── README.md                 # 仓库说明与安装指引
```

## Skill 规范

### 目录结构

每个 skill 位于 `skills/<category>/<skill-name>/`：

- `<category>`：`creative`、`development`、`learning`、`meta` 之一，与 `skills/` 一级目录对应
- `<skill-name>`：英文短横线命名（kebab-case）

### SKILL.md frontmatter

`SKILL.md` 必须包含合法的 YAML frontmatter：

```markdown
---
name: my-skill-name
description: 说明该 skill 的用途与触发场景，描述应具体、可触发
---

# 标题

正文指令...
```

要求：

- `name` 必填，且必须与 skill 目录名完全一致
- `description` 必填，说明「做什么」与「何时使用」，建议包含触发关键词
- 可选的 `metadata.triggers` 用于补充触发词

## 基础设施

### Marketplace 同步

`.claude-plugin/marketplace.json` 由 `scripts/sync_marketplace.py` 自动生成，按分类生成插件（`<category>-tools`），**禁止手动编辑**。

常用命令：

```bash
# 重新生成 marketplace.json
python3 scripts/sync_marketplace.py

# 仅校验，不写入（提交前/CI 使用）
python3 scripts/sync_marketplace.py --check

# 查看扫描到的 skill 列表
python3 scripts/sync_marketplace.py --verbose
```

## 新增 skill 流程

1. 创建 `skills/<category>/<skill-name>/SKILL.md`，frontmatter 含合法的 `name` 与 `description`
2. 运行 `python3 scripts/sync_marketplace.py` 同步 marketplace
3. 更新 `README.md`：
   - 在对应分类的技能表格中新增一行（中文描述）
   - 更新「Repository Structure」结构图
   - 如需要，补充「Usage」触发示例
4. 运行 `python3 scripts/sync_marketplace.py --check` 确认校验通过
5. 遵循 `AGENTS.md` 的 Git 提交规范提交：
   ```
   feat(skills): 添加 xxx 技能
   ```

## 校验清单

提交前确认：

- [ ] SKILL.md frontmatter 合法（`name` 与目录名一致、`description` 非空）
- [ ] `python3 scripts/sync_marketplace.py --check` 通过
- [ ] README 技能表格与结构图已更新
- [ ] 提交信息符合 `<type>(<scope>): <description>` 格式
- [ ] 无调试代码与无关文件
