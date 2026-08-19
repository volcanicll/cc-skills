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

Then install the plugin:
```
1. Run: /plugin marketplace
2. Select "volcanic-skills"
3. Select "development-tools"
4. Select "Install now"
```

### Direct Installation

```bash
/plugin install development-tools@volcanic-skills
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
| **commit-work-items** | 从 Git 仓库 commit 信息生成工作项并导出到研发云 Excel 模板。支持工时报表整理、批量生成研发云导入工作项、自动估算开发工时 |
| **git-history-cleaner** | 清理 Git 仓库历史中的大文件，分析仓库体积、识别问题文件、使用 git-filter-repo 重写历史并压缩仓库 |

### Creative (创意设计)

| Skill | Description |
|-------|-------------|
| **naive-doodle-avatar** | 将真人肖像照片转换为可爱、儿童风、手绘风格的 chibi 涂鸦头像，保留发型、眼镜、脸型、表情、配饰等识别特征 |

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
│   │   └── naive-doodle-avatar/   # Photo to hand-drawn doodle avatar
│   ├── development/           # Development tools
│   │   ├── commit-work-items/     # Git commit to work items generator
│   │   └── git-history-cleaner/   # Git repository history cleaner
│   ├── learning/              # Learning & education
│   │   └── exam-learning-assistant/ # Exam practice automation
│   └── meta/                  # Meta tooling
│       └── skill-manager/         # Skills package manager
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

## Contributing

This is a personal skills repository. Feel free to fork and adapt for your own use.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- **Repository:** https://github.com/volcanicll/cc-skills
- **Agent Skills Spec:** https://agentskills.io