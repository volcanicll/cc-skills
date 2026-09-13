---
name: git-history-cleaner
description: Clean and optimize Git repositories by removing large files from history. Use when Git repository is too large (over 100MB .git directory), when build artifacts like dist.tar.gz bloat the repository, or when you need to permanently remove sensitive files from Git history. This skill analyzes repository size, identifies problematic files, removes them from history using git-filter-repo, and compresses the repository.
metadata:
  category: development
---

# Git History Cleaner

Remove large files and bloat from Git repository history to dramatically reduce repository size.

## Quick Start

```bash
# 1. Analyze repository
du -sh .git
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '/^blob/ {printf "%15d %s\n", $3, $4}' | sort -rn | head -20

# 2. Clean history
python3 -m git_filter_repo --path <filename> --invert-paths --force

# 3. Compress
git reflog expire --expire=now --all && git gc --aggressive --prune=now
```

## Workflow

### Step 1: Analyze Repository Size

Check current repository size and identify problematic files:

```bash
# Check total .git size
du -sh .git

# Get detailed statistics
git count-objects -vH

# Find largest files in history
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '/^blob/ {printf "%15d %s\n", $3, $4}' | sort -rn | head -30
```

**Interpret results:**
- .git > 100MB: Consider cleanup
- .git > 500MB: Cleanup recommended
- .git > 1GB: Urgent cleanup needed

### Step 2: Identify Problem Files

Analyze which files contribute most to repository size:

```bash
# Count versions of a specific file in history
git log --all --oneline --name-only | grep -E "<filename>" | wc -l

# List commits containing the file
git log --all --oneline --name-only | grep -B1 "<filename>" | grep -E "^[a-f0-9]+" | sort -u

# Calculate total size across all branches
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '/^blob/ {if($4 ~ "<filename>") size+=$3} END {printf "Total: %.2f MB\n", size/1024/1024}'
```

**Common problematic files:**
- `dist.tar.gz`, `build.tar.gz` - Build artifacts
- `node_modules/`, `vendor/` - Dependencies (should be in .gitignore)
- `*.zip`, `*.tar` - Archive files
- Database dumps, backups

### Step 3: Confirm User Intent

⚠️ **CRITICAL**: History removal rewrites Git history. Always confirm before proceeding.

**Ask the user:**
1. Confirm they understand this rewrites history
2. Confirm all team members will need to re-clone
3. Confirm which files to remove

**Example:**
> "清理 <filename> 历史记录将重写 Git 历史，需要所有协作者重新克隆仓库。确定要继续吗？"

### Step 4: Install git-filter-repo

Check and install if needed:

```bash
# Check if installed
python3 -m git_filter_repo --help 2>/dev/null || pip3 install git-filter-repo
```

### Step 5: Remove Files from History

```bash
# Remove single file
python3 -m git_filter_repo --path <filename> --invert-paths --force

# Remove multiple files
python3 -m git_filter_repo --path <file1> --path <file2> --invert-paths --force

# Remove directory
python3 -m git_filter_repo --path <directory>/ --invert-paths --force
```

**What happens:**
- File is removed from **ALL commits in ALL branches** (git-filter-repo works on all refs by default)
- Commits are rewritten with new hashes
- Remote is automatically removed (safety measure)

**⚠️ Critical:** git-filter-repo automatically processes ALL branches and tags. You don't need to specify branches separately.

### Step 6: Compress Repository

```bash
# Expire reflog and garbage collect
git reflog expire --expire=now --all && git gc --aggressive --prune=now
```

### Step 7: Verify Results

```bash
# Check new size
du -sh .git
git count-objects -vH

# Verify file removed from ALL branches
git log --all --pretty=format: --name-only | grep "<filename>"

# Verify only target file was removed
git log --all --pretty=format: --name-only | sort -u | head -30

# Create bundle to test actual transfer size
git bundle create /tmp/test-repo.bundle --all
ls -lh /tmp/test-repo.bundle
```

**Expected results:**
- `.git` should be < 50MB for typical projects
- Bundle file should be similar to `.git` size
- No matches for removed filename

### Step 8: Push to Remote (Optional)

⚠️ **WARNING**: Force push rewrites remote history. All team members must re-clone.

```bash
# Re-add remote (git-filter-repo removes it)
git remote add origin <remote-url>

# Verify remote URL
git remote -v

# Force push all branches and tags
git push origin --force --all
git push origin --force --tags
```

**After pushing, notify team:**
```bash
# Team members need to:
cd ..
mv repo-name repo-name.backup
git clone <remote-url>
```

**⚠️ Important: Remote may remain slow temporarily**
- Git servers often delay garbage collection after force push
- Large objects may remain on server for hours to days
- Contact server admin to run `git gc --aggressive --prune=now` on server if needed

## Resources

### references/

- `common-patterns.md` - Common file patterns that bloat repositories
- `troubleshooting.md` - Solutions for common issues

### scripts/

No scripts included - all commands are standard Git/Bash operations.

## Important Notes

### When NOT to Use

- File is currently needed by the team
- Repository has many active contributors (coordination difficult)
- File contains important historical data
- You only want to remove the file from future commits (use .gitignore instead)

### Alternative: .gitignore

If you only want to stop tracking a file (keep history):

```bash
echo "<filename>" >> .gitignore
git rm --cached <filename>
git commit -m "chore: stop tracking <filename>"
git push
```

### Recovery

If you need to recover removed history:

```bash
# Check reflog before expiry
git reflog

# Reset to previous state (if reflog still exists)
git reset --hard@{n}
```

## Typical Results

| Scenario | Before | After | Reduction |
|----------|--------|-------|-----------|
| Build artifacts (dist.tar.gz) | 2.9 GB | 34 MB | -98.8% |
| Database backups | 1.2 GB | 85 MB | -93% |
| Node_modules in history | 800 MB | 120 MB | -85% |
