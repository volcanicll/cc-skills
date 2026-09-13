# 研发云工作项操作手册（单步 + 全流程）

> 设计原则：**生成工作量、导入（创建）、导出、状态流转都是可独立使用的环节**。
> 你要做哪一步就只看/执行哪一步；`flow` 只是把几步串起来的一键入口（可选），不是必经之路。
> 所有命令 Windows 用 `py -3 scripts\rdc_workflow …` 代替 `python3 scripts/rdc_workflow …`。

## 环境要求（零 pip 依赖）

- Python 3.9+（仅标准库，无需 `pip install`）
- Chrome / Edge / Chromium（`auth` 自动发现/自动启动，或 `--manual` 手动粘贴 Cookie）
- git（`stats` 需要本机已克隆待统计仓库）

## 一次性准备（每个环境做一次）

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

---

## 按需单步（常用场景）

以下每节相互独立：只做你要的那一步，不需要的先跳过。

### A. 只生成工作量 Excel（离线，无需登录）

```bash
# 1) 统计 git 提交（--since/--until 缺省用配置 git_since/git_until 或当月 1 号 ~ 今天）
python3 scripts/rdc_workflow --config rdc-config.yaml stats \
  --since 2026-08-01 --until 2026-08-31 -o commits.json
```
`commits.json` 已自动过滤 merge/test/dist/chore 等噪音。AI 按模块/功能把提交分组为工作项：

```json
{"work_items": [{"title": "前端开发-资金归集-登录：…", "hours": 8,
                 "start": "2026-08-01", "end": "2026-08-05", "description": "…"}]}
```
> 工时规则：AI 分组时单工作项最小 1 小时、最大 24 小时；月度总工时
> 由多个工作项累加，单模块工作量较大时应拆分多个工作项。

```bash
# 2) 生成工作量 Excel（产出「导出结果」格式，状态=新建，编号为空）
python3 scripts/rdc_workflow --config rdc-config.yaml build-excel -i work_items.json -o 营销域8月-示例.xlsx
```
到此**这一步已完成**：拿到 `营销域8月-示例.xlsx` 即可交付/存档，无需登录平台。
> Excel 列遵循平台标准 14 列（`scripts/rdc/schema.py` 单一事实源）；`excel_columns`
> 仅在标准列内增删/排序，新增非标准列会报错。

### B. 只导出工作项（在线，用于月度记录 / 核对 / 作为流转底稿）

```bash
# 按创建时间导出（--since/--until = System_CreatedDate，缺省不加创建时间过滤）
python3 scripts/rdc_workflow --config rdc-config.yaml export -o 导出.xlsx \
  --since 2026-08-01 --until 2026-08-31

# 也可按计划开始时间过滤（--plan-since/--plan-until = DXYJY_PlanStartDate，
# 两者成对按 between 过滤，可叠加创建时间过滤）
python3 scripts/rdc_workflow --config rdc-config.yaml export -o 导出.xlsx \
  --since 2026-08-01 --until 2026-08-31 --plan-since 2026-07-31 --plan-until 2026-08-14
```
导出的 Excel 含「编号」列，可直接作为 `update-status` 的输入（读编号列流转状态）。

### C. 只导入 / 创建（在线）

把**工作量 Excel 创建到研发云**，两种方式等价，按需选择：

```bash
# 方式一（一条命令，推荐）：直接 import 工作量 Excel，编号可保存供后续流转
python3 scripts/rdc_workflow --config rdc-config.yaml import 营销域8月-示例.xlsx \
  --yes --ids-out 8月-ids.json
```
- 输入是 build-excel 的工作量 Excel（含平台不支持列且编号为空）时，`import` 会**自动转换**为导入文件
  （移除更新时间/创建人/创建时间列）再校验、导入，无需手动 `prepare`；
- 若想细控转换（改状态、保留编号更新等），先 `prepare` 再 `import`（方式二）；
- `import` 前自动执行 `validate` 打印"预计新增/更新 N 条"，默认需确认（`--yes` 跳过）；
- 成功后 `--ids-out` 把工作项编号写入 JSON（与 `flow` 的 `ids.json` 同格式），
  之后可直接 `update-status --ids-file 8月-ids.json --status 处理中` 续跑流转。

```bash
# 方式二（分步细控）：prepare → validate → import
python3 scripts/rdc_workflow --config rdc-config.yaml prepare 营销域8月-示例.xlsx -o 导入-新建.xlsx --status 新建
python3 scripts/rdc_workflow --config rdc-config.yaml validate 导入-新建.xlsx   # 只读，显示"预计新增 N 条"
python3 scripts/rdc_workflow --config rdc-config.yaml import 导入-新建.xlsx --yes
```
- 导入失败（`failedItemsSize>0`）时自动把错误报告保存为同目录 `错误报告.xlsx`。
- 注意：含「编号」的文件（如平台导出）按**更新已有项**导入；创建新项需编号为空。

### D. 只流转状态（在线，接口方式，不再走 Excel 导入）

创建后从导入响应提取工作项编号（`bo.taskInfo.succeededItems[].data["1"]`），
用 `update-status` 逐级调用 `updateWorkItems/edit` 接口：

```bash
# 1) 编号来源三选一：
#    ① import --ids-out / flow 保存的编号文件
python3 scripts/rdc_workflow --config rdc-config.yaml update-status --ids-file 8月-ids.json --status 处理中 --dry-run
#    ② 含「编号」列的 Excel（如 export 导出、平台导出）
python3 scripts/rdc_workflow --config rdc-config.yaml update-status 导出.xlsx --status 处理中 --dry-run
#    ③ 直接写编号
python3 scripts/rdc_workflow --config rdc-config.yaml update-status --ids P22TEST0000001-6864,P22TEST0000001-6865 --status 处理中 --dry-run

# 2) 预览无误后执行（默认自然语言确认；非交互/脚本环境必须加 --yes）
python3 scripts/rdc_workflow --config rdc-config.yaml update-status --ids-file 8月-ids.json --status 处理中 --yes
```
- 目标状态不在 `status_flow` 中会直接报错；按 `status_flow` 逐级执行：`处理中 → 已完成 → 已关闭`，不可跳级。
- 每级执行一次 `update-status`；返回 `failedItems` 时核对编号与状态。

### E. 更新已有工作项（在线）

已有编号的工作项要改内容/工时等，导出后修改再按"更新"导入：

```bash
python3 scripts/rdc_workflow --config rdc-config.yaml export -o 底稿.xlsx \
  --since 2026-08-01 --until 2026-08-31
# 编辑底稿后转导入文件：--keep-ids 保留编号（否则编号被清空=创建新项）
python3 scripts/rdc_workflow --config rdc-config.yaml prepare 底稿.xlsx -o 更新.xlsx --keep-ids
python3 scripts/rdc_workflow --config rdc-config.yaml import 更新.xlsx --yes
```

---

## 一键全流程（可选）

确认要做"创建 + 逐级流转"整套时才用；仍默认 dry-run，加 `--yes` 执行：

```bash
# 全流程：导入（创建） + 逐级流转到已关闭
python3 scripts/rdc_workflow --config rdc-config.yaml flow --src 营销域8月-示例.xlsx --out-dir flow --yes

# 只创建（编号保存到 flow/ids.json，供后续单步/续跑流转）
python3 scripts/rdc_workflow --config rdc-config.yaml flow --src 营销域8月-示例.xlsx --out-dir flow --mode import --yes

# 只流转（读 flow/ids.json，或 --ids 指定编号）——中途失败后从最后成功状态续跑，
# 不会重复创建/重放已流转状态
python3 scripts/rdc_workflow --config rdc-config.yaml flow --out-dir flow --mode status --yes
```
> 也可以组合单步命令达到同样效果：`import --ids-out` 等价 `flow --mode import`；
> `update-status` 逐级执行等价 `flow --mode status`（后者自动断点续跑）。

## 月度绩效自评

基于工作项/工时生成 100 字以内自评，要点：主导模块、完成功能、保障交付。

## 常见问题

| 现象 | 原因 / 处理 |
|---|---|
| 我只想导出/生成，为什么让我跑完整流程？ | 各环节本就独立：生成用 A、导出用 B、导入用 C、流转用 D，按需执行即可；`flow` 仅在你确认要整套时才用 |
| `import` 提示"已自动转换为导入文件" | 输入是含平台不支持列（更新时间/创建人/创建时间）且编号为空的工作量 Excel；工具已先移除这些列再导入，无需手动 `prepare` |
| 导入报"工作流不存在" | 状态名错误或跳级。核对 `status_flow` 与实际平台状态，逐级流转 |
| 校验提示"列选项不能包含…" | 平台不支持导入该列（更新时间/创建人/创建时间），`prepare` 已默认移除；直接 `import` 未 prepare 的文件会自动转换 |
| 导入 `failedItemsSize>0` | 工具自动保存错误报告为 `错误报告.xlsx` 查看具体原因；常见为单据被修改，重新导出最新文件再导入 |
| `update-status` 返回 failedItems | 编号错误 / 状态非法 / 跳级；核对编号与 `status_flow`，先用 `--dry-run` 预览 |
| 流转时没有编号 | 新创建工作项的编号在导入响应里；`import --ids-out` 或 `flow --mode import` 会落盘编号文件，供 `update-status --ids-file` / `flow --mode status` 使用 |
| `check-excel` 显示"更新"而非"新增" | 文件含编号=更新已有项；创建新项需编号为空（`prepare` 默认清空编号） |
| CDP 连接 403 | 使用 suppress_origin（工具已内置）；勿用 agent-browser 自带的 Origin 头连接 |
| 未发现调试端口 | 直接运行 `auth` 自动启动浏览器；或 `auth --manual` 粘贴 Cookie |
| 自动启动后未登录 | 在弹出的浏览器窗口完成登录，工具会等待 `auth_wait_seconds`（默认 120s）自动提取 |
| 鉴权过期 | 重新运行 `auth`；`doctor` 可提前检查时效 |
| 提示找不到模块 `websocket` 等 | 本工具已零依赖，无需安装；如残留旧脚本请用本版本 scripts/ |
