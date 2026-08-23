# Volcanic's Claude Skills

> Personal collection of Claude Agent Skills for development productivity and workflow automation.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude_Code-compatible-blue.svg)](https://claude.ai/code)

## Overview

This repository contains my personal collection of Claude Agent Skills - modular, self-contained packages that extend Claude's capabilities with specialized knowledge, workflows, and tools.

## What are Skills?

Skills are folders of instructions, scripts, and resources that Claude loads dynamically to improve performance on specialized tasks. Each skill is self-contained with a `SKILL.md` file containing instructions and metadata.

For more information about the Agent Skills standard, visit [agentskills.io](https://agentskills.io).

## Installation

### Via Claude Code Marketplace

```bash
/plugin marketplace add volcanicll/cc-skills
```

The marketplace provides the following plugins (one per skill category):

| Plugin | Category | Skills |
|--------|----------|--------|
| `creative-tools` | 创意设计 | naive-doodle-avatar, image-to-hand-drawn, photo-to-editorial-poster |
| `development-tools` | 开发工具 | git-history-cleaner |
| `learning-tools` | 学习教育 | exam-learning-assistant |
| `meta-tools` | 元工具 | skill-manager |

Then install the plugin(s) you need:
```
1. Run: /plugin marketplace
2. Select "volcanic-skills"
3. Select a plugin, e.g. "creative-tools"
4. Select "Install now"
```

### Direct Installation

```bash
# 安装单个插件（例如创意设计工具）
/plugin install creative-tools@volcanic-skills
# 安装全部插件
/plugin install creative-tools@volcanic-skills development-tools@volcanic-skills learning-tools@volcanic-skills meta-tools@volcanic-skills
```

### Manual Installation

```bash
git clone https://github.com/volcanicll/cc-skills.git
cd cc-skills
```

Copy individual skill folders to your Claude skills directory.

## Available Skills

### Development (开发工具)

| Skill | Description |
|-------|-------------|
| **git-history-cleaner** | 清理 Git 仓库历史中的大文件，分析仓库体积、识别问题文件、使用 git-filter-repo 重写历史并压缩仓库 |
| **changelog-writer** | 将 Git 提交记录整理为面向用户的 Release Notes 或 CHANGELOG 条目：按影响分类、合并相关提交、过滤内部噪音 |

### Creative (创意设计)

| Skill | Description |
|-------|-------------|
| **naive-doodle-avatar** | 将真人肖像照片转换为可爱、儿童风、手绘风格的 chibi 涂鸦头像，保留发型、眼镜、脸型、表情、配饰等识别特征 |
| **image-to-hand-drawn** | 将整张照片转换为高质量手绘插图，保留人物、景观、水体、植被、动物、建筑等完整场景元素，仅简化视觉噪点而非移除环境 |
| **photo-to-editorial-poster** | 将每张照片转换为独立的编辑风海报：3:4 画布，上部保留原照片并做杂志级精修调色，下部将主体重新诠释为轻快、稚拙、复古的手绘编辑插画；支持上下/左右分割与仅插画效果图三种模式，可选对半、不对称、复古边框、卡片式留白等结构变体 |

### Learning (学习教育)

| Skill | Description |
|-------|-------------|
| **exam-learning-assistant** | 考试练习自动化助手。支持多种学习模式、题目匹配、错题复盘、考试报告生成 |

### Meta (元工具)

| Skill | Description |
|-------|-------------|
| **skill-manager** | Agent Skills 包管理器。支持从远程 Git 注册表列出、安装、更新 skills |

## Repository Structure

```
cc-skills/
├── .claude-plugin/
│   └── marketplace.json      # Plugin marketplace configuration
├── skills/                    # Skill directories (categorized)
│   ├── creative/              # Creative & design
│   │   ├── naive-doodle-avatar/   # Photo to hand-drawn doodle avatar
│   │   ├── image-to-hand-drawn/   # Photo to hand-drawn illustration
│   │   └── photo-to-editorial-poster/ # Photo to editorial split poster
│   ├── development/           # Development tools
│   │   ├── changelog-writer/      # Commit history to release notes
│   │   └── git-history-cleaner/   # Git repository history cleaner
│   ├── learning/              # Learning & education
│   │   └── exam-learning-assistant/ # Exam practice automation
│   └── meta/                  # Meta tooling
│       └── skill-manager/         # Skills package manager
├── scripts/
│   └── sync_marketplace.py      # Sync & validate marketplace.json
├── AGENTS.md                   # Project collaboration & skill standards
├── CONTRIBUTING.md             # Contribution guide
├── README.md
├── LICENSE
└── .gitignore
```

## Creating Your Own Skills

Each skill follows a simple structure:

```
skill-name/
├── SKILL.md                   # Required: Metadata and instructions
├── scripts/                   # Optional: Executable scripts
├── references/                # Optional: Documentation and references
└── assets/                    # Optional: Templates and resources
```

### 规范与自动化

开发前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 与 `AGENTS.md` 中的「技能开发规范」。新增或修改 skill 后，运行以下命令同步并校验 marketplace 配置：

```bash
python3 scripts/sync_marketplace.py          # 重新生成 marketplace.json
python3 scripts/sync_marketplace.py --check  # 提交前校验
```

### Minimal SKILL.md Template

```markdown
---
name: my-skill-name
description: A clear description of what this skill does and when Claude should use it
---

# My Skill Name

Instructions for Claude to follow when this skill is active.
```

## Usage

Once installed, skills activate automatically based on context:

**Examples:**
- "根据这个月的 commit 记录生成工时报表"
- "用 skill-manager 查看可用的 skills"
- "帮我安装 baoyu-comic skill"
- "把这张照片变成手绘涂鸦头像"
- "把这张照片变成完整场景的手绘插图"

## Contributing

This is a personal skills repository. Feel free to fork and adapt for your own use.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- **Repository:** https://github.com/volcanicll/cc-skills
- **Agent Skills Spec:** https://agentskills.io