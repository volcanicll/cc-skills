"""
Skill Manager

Agent Skills 的包管理器。支持列出、安装和更新来自远程 Git 仓库的 skills。

Example:
    >>> from skill_manager import SkillManager
    >>> manager = SkillManager()
    >>> manager.list_skills()
    >>> manager.install_skill("commit-work-items")
    >>> manager.update_all()
"""

__version__ = "1.0.0"

from .manager import SkillManager

__all__ = [
    "__version__",
    "SkillManager",
]
