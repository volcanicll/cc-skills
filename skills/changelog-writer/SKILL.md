---
name: changelog-writer
category: development
description: Turn raw git commit history into polished, user-facing release notes or a CHANGELOG entry. Use when preparing a release, writing changelog entries, summarizing commits between two tags, generating "What's Changed" sections, or when asked to write release notes / 更新日志 / 发版说明. Groups commits by type, translates technical changes into user benefits, and outputs Keep a Changelog-compatible Markdown.
metadata:
  triggers:
    - release notes
    - changelog
    - 更新日志
    - 发版说明
    - what's changed
---

# Changelog Writer

Transform messy git commit history into clean, readable release notes that users actually want to read.

## Core Principles

1. **User-facing, not commit-facing.** "fix(api): handle nil pointer on retry" becomes "Fixed a crash when retrying a failed request". Internal refactors are grouped under a brief "Internal" note or omitted entirely.
2. **Group by impact.** Use the Keep a Changelog categories: `Added`, `Changed`, `Fixed`, `Removed`, plus `Security` when relevant. Order by user impact: Added → Changed → Fixed → Removed.
3. **Never invent changes.** Every bullet must trace back to at least one commit or diff. If the commit message is ambiguous, inspect the diff before describing it.
4. **One line per change.** Merge related commits (e.g. five commits for one feature) into a single bullet.

## Workflow

### Step 1: Determine the Range

Identify the commit range to summarize:

```bash
# Between two tags
git log --oneline v1.2.0..HEAD

# Or by date
git log --oneline --since="2 weeks ago"

# With full messages and bodies for context
git log v1.2.0..HEAD --pretty=format:"%h %s%n%b---"
```

If no range is specified, default to the latest tag → HEAD. If no tags exist, use the last 20-30 commits and confirm the scope with the user.

### Step 2: Triage Commits

For each commit, classify by conventional-commit prefix (or infer from the message):

| Prefix | Category | Notes |
|--------|----------|-------|
| `feat` / `feature` | Added | Lead with the user benefit |
| `fix` | Fixed | Describe the symptom that is gone |
| `perf` | Changed | Mention measurable improvement if known |
| `refactor`, `chore`, `ci`, `build` | Internal | Omit unless behavior visibly changed |
| `docs` | Internal | Omit unless docs ship to users |
| `test`, `style` | Internal | Omit |
| `security` / CVE fixes | Security | Always include |

Skip merge commits and bot commits (dependabot, renovate) unless they close a user-visible issue.

### Step 3: Inspect Ambiguous Diffs

When a commit message is vague ("update stuff", "wip"), check what actually changed:

```bash
git show <hash> --stat        # files touched
git show <hash> -- <file>     # specific diff
```

Describe the observable behavior change, not the implementation.

### Step 4: Write the Output

Default format (Keep a Changelog style):

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- Feature name: one-sentence user benefit (#PR)

### Changed
- ...

### Fixed
- ...

### Removed
- ...
```

Rules for bullets:
- Start with a verb in past tense ("Added", "Fixed", "Improved") or a noun phrase
- Include the PR/issue number in parentheses when available
- No commit hashes in the final output
- Match the language of the project's existing changelog (check `CHANGELOG.md` first); default to English, switch to Chinese if the project's changelog or user request is in Chinese

### Step 5: Deliver

Ask (or infer) the delivery target:

- **CHANGELOG.md**: prepend a new `## [version]` section under the header, following any existing format. Create the file with the standard Keep a Changelog header if missing.
- **GitHub Release**: output a standalone Markdown block ready to paste into the release editor, optionally with a "Full Changelog" link: `https://github.com/<owner>/<repo>/compare/<old-tag>...<new-tag>`
- **Chat summary**: a compact version with emoji section headers (✨ Added / 🔧 Changed / 🐛 Fixed) for Slack/WeChat announcements

## Quality Checklist

Before delivering, verify:
- [ ] Every bullet traces to a real commit or diff
- [ ] No internal-only noise (refactors, CI, test churn) in user-facing sections
- [ ] Related commits merged into single bullets
- [ ] Language matches the project's changelog convention
- [ ] Version number and date are correct (or clearly marked as draft)

## References

- [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) — category and format standard
- [Conventional Commits](https://www.conventionalcommits.org/) — commit prefix reference
