#!/usr/bin/env python3
"""Run all quality checks and unit tests across the repository.

Checks performed:
1. Marketplace synchronization check (scripts/sync_marketplace.py --check)
2. Python compilation check (py_compile across all .py files)
3. Markdown relative link integrity check
4. Test suites:
   - exam-learning-assistant (test_question_matcher.py)
   - skill-manager (test_manager.py)
   - rdc-work-items (run_all.py)

Usage:
    python3 scripts/verify_all.py
"""

from __future__ import annotations

import os
import py_compile
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def check_marketplace() -> bool:
    print("▶ 1. Checking marketplace sync...")
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "sync_marketplace.py"), "--check"]
    res = subprocess.run(cmd, cwd=REPO_ROOT)
    if res.returncode != 0:
        print("❌ Marketplace sync check failed.")
        return False
    print("✅ Marketplace sync check passed.\n")
    return True


def check_py_compile() -> bool:
    print("▶ 2. Checking Python syntax via py_compile...")
    py_files = sorted(
        p for p in REPO_ROOT.glob("**/*.py")
        if ".git" not in p.parts and "__pycache__" not in p.parts
    )
    errors = 0
    for p in py_files:
        try:
            py_compile.compile(str(p), doraise=True)
        except py_compile.PyCompileError as e:
            print(f"❌ Syntax error in {p.relative_to(REPO_ROOT)}: {e}")
            errors += 1
    if errors:
        print(f"❌ Found {errors} Python syntax errors.")
        return False
    print(f"✅ All {len(py_files)} Python files compiled successfully.\n")
    return True


def check_markdown_links() -> bool:
    print("▶ 3. Checking Markdown relative links...")
    broken: list[tuple[str, str, str]] = []
    for md in REPO_ROOT.glob("**/*.md"):
        if ".git" in md.parts:
            continue
        text = md.read_text(encoding="utf-8", errors="ignore")
        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)
        for link_text, url in links:
            url = url.strip()
            if (
                url.startswith("http://")
                or url.startswith("https://")
                or url.startswith("#")
                or url.startswith("mailto:")
            ):
                continue
            target = url.split("#")[0]
            if not target:
                continue
            target_path = (md.parent / target).resolve()
            if not target_path.exists():
                broken.append((str(md.relative_to(REPO_ROOT)), link_text, url))

    if broken:
        print(f"❌ Found {len(broken)} broken link(s):")
        for src, txt, target in broken:
            print(f"   {src}: [{txt}]({target})")
        return False
    print("✅ All markdown links are valid.\n")
    return True


def run_unit_tests() -> bool:
    print("▶ 4. Running skills unit tests...")
    test_commands = [
        (
            "exam-learning-assistant",
            [sys.executable, str(REPO_ROOT / "skills" / "exam-learning-assistant" / "tests" / "test_question_matcher.py")],
            REPO_ROOT,
        ),
        (
            "skill-manager",
            [sys.executable, "-m", "unittest", "discover", "-s", str(REPO_ROOT / "skills" / "skill-manager" / "tests")],
            REPO_ROOT,
        ),
        (
            "rdc-work-items",
            [sys.executable, str(REPO_ROOT / "skills" / "rdc-work-items" / "tests" / "run_all.py")],
            REPO_ROOT,
        ),
    ]

    all_passed = True
    for name, cmd, cwd in test_commands:
        print(f"--- Running {name} tests ---")
        res = subprocess.run(cmd, cwd=cwd)
        if res.returncode != 0:
            print(f"❌ {name} tests failed.")
            all_passed = False
        else:
            print(f"✅ {name} tests passed.\n")

    return all_passed


def main() -> int:
    print(f"=== Running full verification for cc-skills ===\n")
    steps = [
        check_marketplace,
        check_py_compile,
        check_markdown_links,
        run_unit_tests,
    ]

    for step in steps:
        if not step():
            print("\n❌ Verification FAILED!")
            return 1

    print("\n🎉 ALL CHECKS PASSED!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
