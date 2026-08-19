# 项目协作规范

## 语言

- 沟通与说明使用中文
- 提交信息描述使用英文
- 变量、文件命名使用英文

## Git 提交规范（强制）

每次提交必须遵循以下规范，不得例外。

### 格式

```
<type>(<scope>): <description>
```

- `<type>`：必填，见下方枚举
- `<scope>`：可选，影响范围（如 `skill-manager`、`commit-work-items`、`docs`）
- `<description>`：英文，简洁描述本次改动做了什么

### Type 枚举

| Type | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 bug |
| `chore` | 构建/工具链相关 |
| `refactor` | 重构 |
| `docs` | 文档 |
| `style` | 代码风格（不影响功能） |
| `test` | 测试 |
| `perf` | 性能优化 |

### 示例

```
feat(user): add user login feature
fix(api): fix API call timeout issue
docs: update README documentation
refactor(skill-manager): refactor package management logic
```

### 规则

1. 小步提交，频繁提交，每个提交只做一件事
2. 不添加 `Co-Authored-By` 等署名行，保持信息简洁
3. 提交前运行 lint 检查，确保无调试代码（console.log 等）
4. 只提交与本次改动相关的文件，不提交无关内容与密钥

## 检查清单

提交前确认：
- [ ] 代码通过 lint 检查
- [ ] 提交信息符合上述格式
- [ ] 无调试代码与注释掉的代码
- [ ] 新文件已加入版本控制

## 技能开发规范（强制）

### 目录结构

每个 skill 位于 `skills/<category>/<skill-name>/`：

- `<category>`：分类名，可选值为 `creative`、`development`、`learning`、`meta`，与 `skills/` 下的一级目录对应
- `<skill-name>`：英文短横线命名（kebab-case），例如 `image-to-hand-drawn`

每个 skill 必须包含 `SKILL.md`，且 frontmatter 满足以下要求：

- `name`：必填，必须与 skill 目录名一致
- `description`：必填，说明该 skill 的用途与触发场景

### Marketplace 维护

- `.claude-plugin/marketplace.json` 由脚本生成，**禁止手动编辑**
- 新增、删除或重命名 skill 后，必须运行同步脚本重新生成：
  ```bash
  python3 scripts/sync_marketplace.py
  ```
- 提交前运行校验，确保 marketplace 与 `skills/` 目录一致：
  ```bash
  python3 scripts/sync_marketplace.py --check
  ```

### 新增 skill 流程

1. 创建 `skills/<category>/<skill-name>/SKILL.md`，frontmatter 含合法的 `name` 与 `description`
2. 运行 `python3 scripts/sync_marketplace.py` 同步 marketplace
3. 更新 `README.md` 中的技能表格与仓库结构图
4. 运行 `python3 scripts/sync_marketplace.py --check` 确认校验通过
5. 按本文件的 Git 提交规范提交
