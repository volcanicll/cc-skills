# 月度工作量录入完整流程

## 环境要求（零 pip 依赖）

- Python 3.9+（仅标准库，无需 `pip install`）
- Chrome / Edge / Chromium（`auth` 自动发现/自动启动，或 `--manual` 手动粘贴 Cookie）
- git（本机已克隆待统计仓库）

## 准备（一次性）

> 原则：**先获取登录信息，缺失的配置再由工具以自然语言提示你补齐**，
> 不再要求先记住一长串命令。

1. 提取登录信息（三种方式，按需选择）：
   - 自动：`python3 scripts/rdc_workflow auth`
     - 已开调试端口的浏览器会被自动发现复用（保持日常登录态）；
     - 没有时自动启动带调试端口的浏览器：优先用 `chrome_profile_dir`（复用登录态，
       但该目录被占用时回退到独立配置目录，首次需登录一次），打开研发云页面并等待登录；
     - 不想自动启动：加 `--no-launch`（未发现调试端口直接报错）
   - 手动：`python3 scripts/rdc_workflow auth --manual`
     - 浏览器 F12 → Network → 任意 srdcloud.cn 请求 → 复制 Cookie 头粘贴即可
   - Windows 用 `py -3 scripts\rdc_workflow …` 代替 `python3 scripts/rdc_workflow`
   - 登录信息（员工号/项目/团队等）从浏览器自动提取，保存到
     `~/.config/rdc-work-items/auth.json`（Windows `%APPDATA%\rdc-work-items\auth.json`）
2. 补齐配置：登录信息提取后，工具会检查 `workspace/project_id/team_id/tenant_id/api_key`、
   `assignee_emp_no/assignee_name/team_name`、`git_author`、`repos` 等是否齐全；
   缺失项会以**自然语言**逐个提示你提供（终端下直接输入即可），并询问是否保存为全局配置
   `~/.config/rdc-work-items.yaml`（Windows `%APPDATA%\rdc-work-items.yaml`），之后自动加载，无需 `--config`。
   - 非交互环境（脚本/Agent）下会列出缺失项后退出，由使用者补充后重试；
   - 也可以一次性走配置向导：`python3 scripts/rdc_workflow setup-config`
     （回车用默认值；非交互用 `--no-input --workspace … --api-key … --repos …`）；
   - 可选：复制 `config.example.yaml` → 本地 `rdc-config.yaml` 覆盖（优先级高于全局）；
   - `status_flow` / `wic_base_url` 等默认即可；如需调整见 `config.example.yaml` 注释
3. （推荐）环境自检：`python3 scripts/rdc_workflow doctor`
   - 只读检查：配置完整性、登录态时效、浏览器调试端口、git 仓库是否可访问

## 每月流程

### 1. 统计提交
```bash
python3 scripts/rdc_workflow --config rdc-config.yaml stats \
  --since 2026-08-01 --until 2026-08-31 -o commits.json
```
`--since/--until` 缺省用配置 `git_since/git_until` 或当月 1 号 ~ 今天。
输出每个仓库的业务提交（自动过滤 merge/test/dist/chore 等噪音）。AI 按模块/功能人工分组为工作项。

### 2. 生成工作量 Excel
`work_items.json` 格式（**单工作项 `hours` 必须为 1~24 小时**，超出会校验失败）：
```json
{"work_items": [{"title": "前端开发-资金归集-登录：…", "hours": 8,
                 "start": "2026-08-01", "end": "2026-08-05", "description": "…"}]}
```
> 工时规则：AI 分组时单工作项最小 1 小时、最大 24 小时；月度总工时
> 由多个工作项累加，单模块工作量较大时应拆分多个工作项。
```bash
python3 scripts/rdc_workflow --config rdc-config.yaml build-excel -i work_items.json -o 营销域8月-示例.xlsx
```

### 3. 导入（创建）
```bash
python3 scripts/rdc_workflow --config rdc-config.yaml prepare 营销域8月-示例.xlsx -o 导入-新建.xlsx --status 新建
python3 scripts/rdc_workflow --config rdc-config.yaml validate 导入-新建.xlsx   # 只读，显示"预计新增 N 条"
python3 scripts/rdc_workflow --config rdc-config.yaml import 导入-新建.xlsx     # 导入前自动校验并确认
# 或直接跳过确认：import 导入-新建.xlsx --yes
```
- `import` 会自动先执行 `validate` 打印"预计新增/更新 N 条"，默认需输入 `y` 确认（`--yes` 跳过）；
- 导入失败（`failedItemsSize>0`）时自动把错误报告保存为同目录 `错误报告.xlsx`。

### 4. 状态流转（接口方式，不再走 Excel 导入）
创建后从导入响应提取工作项编号（`bo.taskInfo.succeededItems[].data["1"]`），
用 `update-status` 逐级调用 `updateWorkItems/edit` 接口：

```bash
# 先预览（自然语言确认后再执行）
python3 scripts/rdc_workflow --config rdc-config.yaml update-status 导出.xlsx --status 处理中 --dry-run
python3 scripts/rdc_workflow --config rdc-config.yaml update-status 导出.xlsx --status 处理中
# 或直接指定编号
python3 scripts/rdc_workflow --config rdc-config.yaml update-status --ids P22TEST0000001-6864,P22TEST0000001-6865 --status 已完成
```

逐级执行：`处理中 → 已完成 → 已关闭`（按 `status_flow`，不可跳级）。

### 5. 全流程（一步到位 / 多模式）
```bash
# 全流程：导入 + 逐级流转（默认 dry-run，--yes 执行）
python3 scripts/rdc_workflow --config rdc-config.yaml flow --src 营销域8月-示例.xlsx --out-dir flow --yes

# 只创建（编号保存到 flow/ids.json，供续跑）
python3 scripts/rdc_workflow --config rdc-config.yaml flow --src 营销域8月-示例.xlsx --out-dir flow --mode import --yes

# 只流转（读 flow/ids.json，或 --ids 指定编号）——中途失败后可安全重跑，不会重复创建
python3 scripts/rdc_workflow --config rdc-config.yaml flow --out-dir flow --mode status --yes
```

### 6. 导出（可选，用于月度记录）
```bash
python3 scripts/rdc_workflow --config rdc-config.yaml export -o 导出.xlsx \
  --since 2026-08-01 --until 2026-08-31
```

### 7. 月度绩效自评
基于工作项/工时生成 100 字以内自评，要点：主导模块、完成功能、保障交付。

## 常见问题

| 现象 | 原因 / 处理 |
|---|---|
| 导入报"工作流不存在" | 状态名错误或跳级。核对 `status_flow` 与实际平台状态，逐级流转 |
| 校验提示"列选项不能包含…" | 平台不支持导入该列（更新时间/创建人/创建时间），prepare 已默认移除 |
| 导入 `failedItemsSize>0` | 工具自动保存错误报告为 `错误报告.xlsx` 查看具体原因；常见为单据被修改，重新导出最新文件再导入 |
| `update-status` 返回 failedItems | 编号错误 / 状态非法 / 跳级；核对编号与 `status_flow`，先用 `--dry-run` 预览 |
| `check-excel` 显示"更新"而非"新增" | 文件含编号=更新已有项；创建新项需编号为空 |
| CDP 连接 403 | 使用 suppress_origin（工具已内置）；勿用 agent-browser 自带的 Origin 头连接 |
| 未发现调试端口 | 直接运行 `auth` 自动启动浏览器；或 `auth --manual` 粘贴 Cookie |
| 自动启动后未登录 | 在弹出的浏览器窗口完成登录，工具会等待 `auth_wait_seconds`（默认 120s）自动提取 |
| 鉴权过期 | 重新运行 `auth`；`doctor` 可提前检查时效 |
| 提示找不到模块 `websocket` 等 | 本工具已零依赖，无需安装；如残留旧脚本请用本版本 scripts/ |
