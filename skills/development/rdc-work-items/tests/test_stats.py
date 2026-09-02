# -*- coding: utf-8 -*-
"""stats（git 提交统计）测试：python3 tests/test_stats.py"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from rdc import stats


def test_default_range():
    since, until = stats.default_range(datetime.date(2026, 9, 2))
    assert since == "2026-09-01"
    assert until == "2026-09-02"
    # 当月 1 号
    since, until = stats.default_range(datetime.date(2026, 9, 1))
    assert since == "2026-09-01" and until == "2026-09-01"


def test_extract_requires_repos():
    try:
        stats.extract({"git_author": "a", "repos": []}, "2026-09-01", "2026-09-02")
        raise AssertionError("未配置 repos 应报错")
    except ValueError as e:
        assert "repos" in str(e)


def _make_repo():
    """建一个 2 条提交（alice/bob）的临时 git 仓库。

    提交时间固定为 2026-09-01（与测试查询区间 09-01~09-02 对齐），
    避免因“今天”变化导致提交落在区间外而统计不到。
    """
    import subprocess
    import tempfile
    repo = tempfile.mkdtemp(prefix="rdc-repo-")
    when = "2026-09-01T10:00:00 +0800"
    for name, content in (("alice", "1"), ("bob", "2")):
        subprocess.run(["git", "-C", repo, "init", "-q"], check=True)
        subprocess.run(["git", "-C", repo, "config", "user.email", "t@t.t"], check=True)
        subprocess.run(["git", "-C", repo, "config", "user.name", name], check=True)
        fn = os.path.join(repo, f"f-{content}.txt")
        with open(fn, "w", encoding="utf-8") as f:
            f.write(content)
        subprocess.run(["git", "-C", repo, "add", "."], check=True)
        env = dict(os.environ, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
        subprocess.run(["git", "-C", repo, "commit", "-qm", f"feat: {name}"],
                       check=True, env=env)
    return repo


def test_extract_placeholder_author_counts_all():
    """git_author 为占位符时视为未配置，统计全部作者（避免误返回 0 条）。"""
    repo = _make_repo()
    r = stats.extract({"git_author": "YOUR_GIT_AUTHOR", "repos": [repo]},
                      "2026-09-01", "2026-09-02")
    assert r["author"] == ""
    assert r["total_business_commits"] == 2
    r2 = stats.extract({"git_author": "alice", "repos": [repo]},
                       "2026-09-01", "2026-09-02")
    assert r2["total_business_commits"] == 1


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("stats tests passed")
