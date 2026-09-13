# -*- coding: utf-8 -*-
"""从 git 仓库提取指定作者/时间段的提交，过滤噪音，输出为 JSON 供 AI 分组为工作项。"""
import datetime
import json
import re
import subprocess

# 噪音提交匹配（合并/测试/构建/配置/文档/临时）
NOISE_PATTERNS = re.compile(
    r"^(merge|pull request|pr#?\d|test|spec|build|dist|chore|ci|config|docs?|readme|changelog|"
    r"style|format|prettier|eslint|refactor type|wip|todo|fixup|squash|"
    r"index on |on dev|untracked|cline checkpoint|qwqw|调试)",
    re.IGNORECASE,
)


def default_range(today=None):
    """默认统计区间：当月 1 号 ~ 今天（stats --since/--until 缺省时使用）。"""
    today = today or datetime.date.today()
    return today.replace(day=1).isoformat(), today.isoformat()


def _git(repo, since, until, author):
    cmd = ["git", "-C", repo, "log",
           "--since", f"{since} 00:00:00", "--until", f"{until} 23:59:59",
           "--all", "--format=%H|%an|%ad|%s", "--date=format:%Y-%m-%d %H:%M"]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        return {"repo": repo, "error": out.stderr.strip(), "commits": []}
    commits = []
    for line in out.stdout.splitlines():
        parts = line.split("|", 3)
        if len(parts) != 4:
            continue
        h, an, ad, msg = parts
        if author and an != author:
            continue
        commits.append({"hash": h, "author": an, "date": ad, "message": msg})
    return {"repo": repo, "commits": commits}


def extract(cfg, since, until, author=None, repos=None, include_noise=False):
    """提取提交；repos 缺省用配置中的 repos。author 缺省用配置 git_author，占位符视为未配置（统计全部作者）。"""
    author = author if author is not None else cfg.get("git_author", "")
    if author and str(author).strip().startswith("YOUR_"):
        author = None  # 占位符 → 不按作者过滤
    repos = repos or cfg.get("repos", [])
    if not repos:
        raise ValueError("未配置 repos（git 仓库列表），请在配置或 --repos 中指定")
    result = {"since": since, "until": until, "author": author or "", "repos": []}
    total = 0
    for repo in repos:
        r = _git(repo, since, until, author)
        commits = r["commits"]
        if not include_noise:
            commits = [c for c in commits if not NOISE_PATTERNS.match(c["message"].strip())]
        r["commits"] = commits
        r["count"] = len(commits)
        total += len(commits)
        result["repos"].append(r)
    result["total_business_commits"] = total
    return result


def dump(result, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return out_path
