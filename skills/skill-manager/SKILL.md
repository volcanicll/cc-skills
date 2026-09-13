---
name: skill-manager
description: Package manager for Agent Skills. Allows listing, installing, and updating skills from remote Git registries locally.
metadata:
  category: meta
  triggers:
    - skill-manager
    - 安装技能
    - 更新技能
    - 列出技能
    - install skill
    - update skills
---

# Skill Manager

A powerful CLI-based package manager for your Agent Skills. It manages synchronization between your local skills folder and remote Git repositories.

## Features

- **Pre-configured Registries**: Comes with standard skill sources (e.g. `cc-skills`) out of the box.
- **Smart Updates**: Automatically detects installed skills and pulls updates for them.
- **Discovery**: List and browse available skills from the cloud.
- **Custom Target**: Supports custom target directory via `--target` or `SKILLS_DIR` environment variable.

## Usage

You can run the python script directly from the repository or from your installed skills folder.

### Commands

**1. List Available Skills**
See what skills are available for installation.

```bash
# In repository:
python3 skills/skill-manager/scripts/manager.py list
# Or if installed in .agent/skills/:
python3 .agent/skills/skill-manager/scripts/manager.py list
```

**2. Install a Skill**
Download and install a specific skill.

```bash
python3 skills/skill-manager/scripts/manager.py install <skill_name>
# Example (with optional custom target directory):
python3 skills/skill-manager/scripts/manager.py install git-history-cleaner --target ~/.claude/skills
```

**3. Update All Skills**
Update all skills that are currently installed locally.

```bash
python3 skills/skill-manager/scripts/manager.py update
```

## Configuration

Configuration is stored in `config/sources.json`. It defines the "Registries" (Git repositories) to check.

```json
{
  "registries": [
    {
      "name": "volcanic-skills",
      "url": "https://github.com/volcanicll/cc-skills",
      "branch": "main",
      "skills_root": "skills",
      "priority": 100
    }
  ]
}
```
