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
- `<scope>`：可选，影响范围（如 `skill-manager`、`docs`）
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

每个 skill 位于 `skills/<skill-name>/`（一级目录存放，不再按分类建子目录）：

- `<skill-name>`：英文短横线命名（kebab-case），例如 `image-to-hand-drawn`

每个 skill 必须包含 `SKILL.md`，且 frontmatter 满足以下要求（符合 VS Code skills 标准规范）：

- `name`：必填，必须与 skill 目录名一致
- `description`：必填，说明该 skill 的用途与触发场景
- `metadata.category`：必填，分类名，可选值为 `creative`、`development`、`learning`、`meta`（置于 `metadata` 下以兼容 VS Code skills schema 校验）

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

1. 创建 `skills/<skill-name>/SKILL.md`，frontmatter 含合法的 `name`、`description` 与 `metadata.category`
2. 运行 `python3 scripts/sync_marketplace.py` 同步 marketplace
3. 更新 `README.md` 中的技能表格与仓库结构图
4. 运行 `python3 scripts/sync_marketplace.py --check` 确认校验通过
5. 按本文件的 Git 提交规范提交

### 元 skill 模板

新 skill 以 `skills/browser-login-session/` 为结构模板（元 skill）：

```
skill-name/
├── SKILL.md           # 精简入口：能力边界、快速开始、工作流、红线
├── manifest.json      # 元数据（名称/版本/依赖/结构）
├── references/        # 详细指引（架构、协议、安全等，按需增减）
├── scripts/           # 核心可执行脚本（优先零第三方依赖）
├── examples/          # 原始输入 → 设计总结 → 用法示例
└── tests/             # 可运行的验证脚本
```

创建新 skill 时按 `browser-login-session/references/skill-authoring.md` 的清单执行：
SKILL.md 保持精简、细节下沉 `references/`、提交前跑测试与同步校验。

### 推送前检查（强制）

每次推送（push）前，必须把以下内容纳入本次提交，未同步不得推送：

1. `README.md`：技能表格、Repository Structure 结构图、Usage 触发示例；
2. `docs/index.html` 落地页：技能总数、分类计数、技能列表与描述；
3. 相关文档：`CONTRIBUTING.md` / `AGENTS.md` 在结构或规范变化时同步；
4. 运行 `python3 scripts/sync_marketplace.py --check` 确认 marketplace 一致；
5. 运行 `python3 scripts/verify_all.py` 确认全量门禁（语法编译、Markdown 链接、各技能单元测试）全部通过。
