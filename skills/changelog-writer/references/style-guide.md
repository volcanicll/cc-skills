# Release Notes Style Guide

Reference examples for writing high-quality changelog entries.

## Bad → Good

| Bad (commit-facing) | Good (user-facing) |
|---|---|
| `fix: fix bug` | Fixed an issue where exported PDFs were missing the last page |
| `refactor(auth): migrate to new token store` | *(omit — no user-visible change)* |
| `feat: add export` | Added CSV export for the usage report (#123) |
| `perf: optimize query` | Search results now load ~3x faster on large workspaces |
| `chore(deps): bump lodash to 4.17.21` | *(omit, or Security if it fixes a CVE)* |

## Merging Related Commits

Five commits like `feat: add drag handle`, `fix: drag handle z-index`, `fix: drag on touch`, `style: drag cursor`, `refactor: extract DragHandle component`
become one bullet:

> Added: drag-and-drop reordering for checklist items (#88)

## Version Bumps

If the range contains only dependency bumps and CI changes with no user-visible impact, say so explicitly rather than producing an empty section:

```markdown
## [1.0.3] - 2026-08-23

Maintenance release. No user-facing changes; internal dependency updates only.
```

## Tone

- Confident but not marketing-speak. "Improved startup time" not "Blazingly fast now!"
- Specific numbers when known ("reduced memory usage by 40%"), vague when not ("reduced memory usage")
- Past tense for everything
