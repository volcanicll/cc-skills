#!/usr/bin/env python3
"""Sync .claude-plugin/marketplace.json from the skills/ directory.

This script is the single source of truth for the marketplace plugin layout:

    skills/<skill>/SKILL.md  ->  plugin "<category>-tools" -> skill "./skills/<skill>"

It validates every SKILL.md frontmatter:
- 'name' required, must match skill directory name
- 'description' required
- 'category' required, must be one of: creative, development, learning, meta

Usage:
    python3 scripts/sync_marketplace.py            # rewrite marketplace.json
    python3 scripts/sync_marketplace.py --check    # verify only, exit non-zero on drift
    python3 scripts/sync_marketplace.py --verbose  # print scanned skills
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "skills"
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"

# Human-readable plugin descriptions (English, shown in Claude Code UI).
PLUGIN_DESCRIPTIONS = {
    "creative": "Creative design tools: photo-to-illustration and avatar generation",
    "development": "Development workflow and productivity tools",
    "learning": "Learning and education tools",
    "meta": "Meta tooling for managing Agent Skills",
}

VALID_CATEGORIES = set(PLUGIN_DESCRIPTIONS.keys())


class SkillError(Exception):
    """Raised when a skill fails validation."""


def _fallback_yaml_parse(text: str) -> dict:
    """Minimal stdlib-only YAML parser for SKILL.md frontmatter."""
    res: dict = {}
    lines = text.splitlines()
    i = 0
    num_lines = len(lines)

    while i < num_lines:
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            key, val = match.groups()
            val = val.strip()
            if not val:
                # Could be a nested dict or list
                nested_lines: list[str] = []
                i += 1
                while i < num_lines:
                    next_line = lines[i]
                    if next_line.strip() and not next_line.startswith(" ") and not next_line.startswith("\t"):
                        break
                    nested_lines.append(next_line)
                    i += 1

                # Check if list or dict
                is_list = any(l.strip().startswith("- ") for l in nested_lines if l.strip())
                if is_list:
                    items: list[str] = []
                    for nl in nested_lines:
                        s = nl.strip()
                        if s.startswith("- "):
                            item_val = s[2:].strip()
                            if len(item_val) >= 2 and item_val[0] in ('"', "'") and item_val[-1] == item_val[0]:
                                item_val = item_val[1:-1]
                            items.append(item_val)
                    res[key] = items
                else:
                    nested_dict = {}
                    for nl in nested_lines:
                        nm = re.match(r"^\s+([A-Za-z0-9_-]+):\s*(.*)$", nl)
                        if nm:
                            nk, nv = nm.groups()
                            nv = nv.strip()
                            if len(nv) >= 2 and nv[0] in ('"', "'") and nv[-1] == nv[0]:
                                nv = nv[1:-1]
                            nested_dict[nk] = nv
                    res[key] = nested_dict
                continue
            else:
                if len(val) >= 2 and val[0] in ('"', "'") and val[-1] == val[0]:
                    val = val[1:-1]
                res[key] = val
        i += 1
    return res


def parse_frontmatter(skill_dir: Path) -> dict:
    """Parse the YAML frontmatter of a SKILL.md file."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise SkillError(f"{skill_dir.relative_to(REPO_ROOT)}: missing SKILL.md")

    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise SkillError(f"{skill_md.relative_to(REPO_ROOT)}: frontmatter must start with '---'")

    end = text.find("\n---", 4)
    if end == -1:
        raise SkillError(f"{skill_md.relative_to(REPO_ROOT)}: frontmatter is not closed with '---'")

    frontmatter_content = text[4:end]
    try:
        import yaml
        meta = yaml.safe_load(frontmatter_content)
    except ImportError:
        meta = _fallback_yaml_parse(frontmatter_content)
    except Exception as exc:
        raise SkillError(f"{skill_md.relative_to(REPO_ROOT)}: invalid YAML frontmatter: {exc}") from exc

    if not isinstance(meta, dict):
        raise SkillError(f"{skill_md.relative_to(REPO_ROOT)}: frontmatter must be a YAML mapping")
    return meta


def validate_skill(skill_dir: Path, verbose: bool) -> dict:
    """Validate one skill and return its normalized metadata."""
    name = skill_dir.name
    meta = parse_frontmatter(skill_dir)

    meta_name = meta.get("name")
    if not meta_name:
        raise SkillError(f"{skill_dir.relative_to(REPO_ROOT)}: frontmatter 'name' is required")
    if meta_name != name:
        raise SkillError(
            f"{skill_dir.relative_to(REPO_ROOT)}: frontmatter name '{meta_name}' "
            f"must match directory name '{name}'"
        )

    category = meta.get("category")
    if not category:
        raise SkillError(
            f"{skill_dir.relative_to(REPO_ROOT)}: frontmatter 'category' is required "
            f"(must be one of: {', '.join(sorted(VALID_CATEGORIES))})"
        )
    if category not in VALID_CATEGORIES:
        raise SkillError(
            f"{skill_dir.relative_to(REPO_ROOT)}: invalid category '{category}', "
            f"must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
        )

    description = meta.get("description")
    if not description:
        raise SkillError(f"{skill_dir.relative_to(REPO_ROOT)}: frontmatter 'description' is required")

    if verbose:
        print(f"  [{category}] {name}: {str(description)[:60]}...")
    return {"name": name, "category": category, "description": str(description)}


def scan_skills(verbose: bool) -> list[dict]:
    """Scan the skills/ tree and return validated skill records."""
    if not SKILLS_ROOT.is_dir():
        raise SkillError(f"{SKILLS_ROOT.relative_to(REPO_ROOT)}: skills directory not found")

    skills: list[dict] = []
    for skill_dir in sorted(p for p in SKILLS_ROOT.iterdir() if p.is_dir() and not p.name.startswith(".")):
        record = validate_skill(skill_dir, verbose)
        skills.append(record)
    return skills


def build_plugins(skills: list[dict]) -> list[dict]:
    """Group scanned skills into one plugin per category."""
    plugins: list[dict] = []
    for category in sorted({s["category"] for s in skills}):
        category_skills = sorted((s for s in skills if s["category"] == category), key=lambda s: s["name"])
        plugins.append(
            {
                "name": f"{category}-tools",
                "description": PLUGIN_DESCRIPTIONS.get(
                    category, f"Tools in the {category} category"
                ),
                "source": "./",
                "strict": False,
                "skills": [f"./skills/{s['name']}" for s in category_skills],
            }
        )
    return plugins


def load_existing_marketplace() -> dict:
    """Load the current marketplace.json, falling back to defaults."""
    if MARKETPLACE_PATH.is_file():
        return json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
    return {
        "name": "volcanic-skills",
        "owner": {"name": "volcanic", "email": "", "url": "https://github.com/volcanicll"},
        "metadata": {
            "description": "Personal collection of Claude Agent Skills",
            "version": "1.0.0",
            "homepage": "https://github.com/volcanicll/cc-skills",
        },
    }


def build_marketplace(skills: list[dict]) -> dict:
    """Build the full marketplace document, preserving existing identity metadata."""
    existing = load_existing_marketplace()
    marketplace = {
        "name": existing.get("name", "volcanic-skills"),
        "owner": existing.get(
            "owner",
            {"name": "volcanic", "email": "", "url": "https://github.com/volcanicll"},
        ),
        "metadata": existing.get(
            "metadata",
            {
                "description": "Personal collection of Claude Agent Skills",
                "version": "1.0.0",
                "homepage": "https://github.com/volcanicll/cc-skills",
            },
        ),
        "plugins": build_plugins(skills),
    }
    return marketplace


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify marketplace.json is up to date")
    parser.add_argument("--verbose", action="store_true", help="print scanned skills")
    args = parser.parse_args()

    try:
        skills = scan_skills(args.verbose)
        expected = build_marketplace(skills)
    except SkillError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1

    if args.verbose and not args.check:
        print(f"Scanned {len(skills)} skills, writing {MARKETPLACE_PATH.relative_to(REPO_ROOT)}")

    if args.check:
        if not MARKETPLACE_PATH.is_file():
            sys.stderr.write(
                f"error: {MARKETPLACE_PATH.relative_to(REPO_ROOT)} is missing; run sync_marketplace.py\n"
            )
            return 1
        current = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
        if current == expected:
            print(f"OK: {MARKETPLACE_PATH.relative_to(REPO_ROOT)} is up to date ({len(skills)} skills)")
            return 0
        sys.stderr.write(
            "error: marketplace.json is out of date. Run: python3 scripts/sync_marketplace.py\n"
        )
        return 1

    MARKETPLACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKETPLACE_PATH.write_text(
        json.dumps(expected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"OK: wrote {MARKETPLACE_PATH.relative_to(REPO_ROOT)} ({len(skills)} skills, {len(expected['plugins'])} plugins)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
