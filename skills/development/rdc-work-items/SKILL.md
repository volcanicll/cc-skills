---
name: rdc-work-items
description: 研发云（srdcloud.cn）工作项月度工作量全流程自动化：从 git 提交统计生成工作量 Excel，通过 CDP 获取登录态鉴权后调用平台接口完成工作项导入、导出与状态流转（新建→处理中→已完成→已关闭）。纯 Python 标准库、零 pip 依赖。所有环境变量（工作区/团队/指派人/状态流/仓库列表等）通过 rdc-config.yaml 自定义。用于"工作量统计/生成工作量excel/导入导出工作项/月度绩效"等请求。
metadata:
  short-description: 研发云工作项导入导出与状态流转自动化
---

# 研发云工作项自动化（rdc-work-items）

按"统计工作量 → 生成 Excel → 导入平台 → 接口逐级流转状态"的月度流程，调用研发云接口完成录入，
避免手工上传下载。脚本位于 `scripts/`，全部变量由 `rdc-config.yaml` 自定义。
**纯 Python 标准库，零 pip 依赖**（WebSocket/HTTP/YAML/Excel 均内置实现）。

## 平台要求

- **操作系统**：macOS / Windows / Linux 均可（Python 脚本跨平台）。
- **运行环境**：Python 3.9+，**无需安装任何第三方包**（标准库即可）。
- **浏览器**：Chrome / Edge / Chromium。`auth` 会自动发现已开调试端口的浏览器；
  没有时自动启动一个带调试端口的浏览器（复用配置的 `chrome_profile_dir` 保持登录态，
  占用中则回退到独立配置目录，首次需登录一次）；也可 `auth --manual` 手动粘贴 Cookie。
- **Windows**：用 `py -3 scripts\rdc_workflow`（或 `scripts/rdc_workflow.cmd`）代替 `python3 scripts/rdc_workflow`；
  在 `rdc-config.yaml` 的 `chrome_profile_dir` 填 Windows 用户数据目录；
  留空时脚本自动按系统探测 Chrome/Edge 的 `DevToolsActivePort` 或 HTTP 探测调试端口。
- **git**：统计提交需要本机已克隆对应仓库，仓库路径在 `rdc-config.yaml` 的 `repos` 中配置。
- **全局配置与鉴权（多平台）**：首次配置写入全局配置
  `~/.config/rdc-work-items.yaml`（Windows 为 `%APPDATA%\rdc-work-items.yaml`）；
  鉴权文件保存到 `~/.config/rdc-work-items/auth.json`（Windows 为 `%APPDATA%\rdc-work-items\auth.json`），
  均不落入项目目录。

## 快速开始

1. 获取登录信息（自动发现调试浏览器；没有则自动启动并等待登录；也可 `auth --manual` 粘贴 Cookie）：
   ```bash
   python3 scripts/rdc_workflow --config rdc-config.yaml auth
   ```
   登录信息（员工号/项目/团队等）会从浏览器自动提取并保存到鉴权文件。
2. 补齐配置：登录信息提取后，若还缺工作区/API Key/团队名称等，工具会以**自然语言**逐个提示你提供，
   并询问是否保存为全局配置（`~/.config/rdc-work-items.yaml`，Windows 为 `%APPDATA%\rdc-work-items.yaml`），
   之后自动加载（无需 `--config`）。也可以运行首次配置向导（回车用默认值，或 `--no-input` 非交互）：
   ```bash
   python3 scripts/rdc_workflow setup-config
   ```
   也支持本地配置：复制 `config.example.yaml` 为 `rdc-config.yaml` 并修改（优先级高于全局）。
3. 环境自检（可选但推荐，检查配置完整性/登录态时效/调试端口/git 仓库）：
   ```bash
   python3 scripts/rdc_workflow doctor
   ```
4. 统计提交（按配置的 `git_author` 过滤噪音；`--since/--until` 缺省用配置或当月）：
   ```bash
   python3 scripts/rdc_workflow --config rdc-config.yaml stats --since 2026-08-01 --until 2026-08-31 -o commits.json
   ```
5. AI 将 `commits.json` 的提交按模块/功能分组为工作项（标题/工时/起止日期/说明），写入 `work_items.json`，
   再生成工作量 Excel：
   ```bash
   python3 scripts/rdc_workflow --config rdc-config.yaml build-excel -i work_items.json -o 营销域8月-示例.xlsx
   ```
6. 全流程（默认 dry-run 只校验，加 `--yes` 才真实执行）：
   ```bash
   python3 scripts/rdc_workflow --config rdc-config.yaml flow --src 营销域8月-示例.xlsx --out-dir flow --yes
   ```
   或分步执行（创建走 Excel 导入，状态流转走接口）：
   ```bash
   ... prepare --status 新建 && validate && import --yes   # 创建（import 默认需确认，--yes 跳过）
   ... update-status 导出.xlsx --status 处理中 --dry-run    # 先预览再执行（也可 --ids 指定编号）
   ... update-status 导出.xlsx --status 已完成
   ... update-status 导出.xlsx --status 已关闭
   ```

## 命令速查

| 命令 | 作用 | 示例（Windows 用 `py -3 scripts\rdc_workflow` 代替） |
|---|---|---|
| `setup-config` | 首次配置向导（写全局配置） | `rdc_workflow setup-config` |
| `doctor` | 环境自检（只读） | `rdc_workflow doctor` |
| `auth` | 提取鉴权（自动启动/手动粘贴） | `rdc_workflow auth` / `auth --manual` |
| `stats` | git 提交统计（供 AI 分组） | `stats --since 2026-08-01 --until 2026-08-31 -o commits.json` |
| `build-excel` | 工作项 JSON → 工作量 Excel | `build-excel -i work_items.json -o 8月.xlsx` |
| `prepare` | 导出格式 → 导入文件（清编号/改状态） | `prepare 8月.xlsx -o 导入-新建.xlsx --status 新建` |
| `validate` | 校验导入文件（只读） | `validate 导入-新建.xlsx` |
| `import` | 导入创建（默认需确认，`--yes` 跳过） | `import 导入-新建.xlsx --yes` |
| `update-status` | 接口流转状态（默认需确认，`--yes` 跳过；`--dry-run` 预览） | `update-status 导出.xlsx --status 处理中 --dry-run` |
| `export` | 导出工作项 Excel | `export -o 导出.xlsx --since 2026-08-01 --until 2026-08-31` |
| `summary` | 查看文件内工作项 | `summary 8月.xlsx` |
| `flow` | 全流程多模式（默认 dry-run） | `flow --src 8月.xlsx --mode full --yes` |
| `--version` | 查看版本 | `rdc_workflow --version` |

`flow` 三种模式（`--mode`，均默认 dry-run，加 `--yes` 执行）：
- `full`（默认）：prepare → validate → import（创建）→ 接口逐级流转；
- `import`：只创建，工作项编号保存到 `--out-dir/ids.json`；
- `status`：只流转状态（读 `--out-dir/ids.json` 或 `--ids` 指定编号），用于断点续跑；每级成功后记录进度，重跑从中断处继续，不会重复创建、不会重放已流转状态。

## 关键规则（安全）

- **配置缺失引导**：平台操作（校验/导入/导出/流转/全流程）前会先检查登录信息与配置；
  缺失时**先获取登录信息**，再把仍缺失的项以自然语言提示你提供（非交互环境会列出缺失项后退出）。
  所有需要你确认的操作（导入、状态流转、保存配置）都用自然语言提问，不再直接展示命令。

- **单工作项工时范围：最小 1 小时、最大不超过 24 小时**。`build-excel` 会强制校验，
  越界/非数字会报错并列出违规项，需拆分后再生成 Excel。
- **编号为空 = 创建新工作项；编号有值 = 更新已有工作项**。切勿重复导入"新建"文件（会重复创建）。
- **状态必须按配置的 `status_flow` 逐级流转**（默认 新建→处理中→已完成→已关闭），
  通过 `updateWorkItems/edit` 接口调用，跳级或状态名错误会报"工作流不存在"。
- **创建**：`import` 前会自动执行 `validate` 并打印"预计新增/更新 N 条"，默认需输入 `y` 确认
  （`--yes` 跳过）；导入返回 `failedItemsSize>0` 时自动下载错误报告保存为本地 `错误报告.xlsx`。
- **状态流转**：`update-status` 从导入响应（`succeededItems[].data["1"]`）或含编号的
  Excel 读取工作项编号，调用接口逐级流转；先 `--dry-run` 预览，默认需自然语言确认后执行（`--yes` 跳过，非交互环境必须加），返回 `failedItems` 时核对编号与状态。
- **续跑安全**：`flow --mode import` 与 `--mode status` 分离，编号落盘 `ids.json`，
  中途失败后重跑 `status` 模式不会重复创建。
- `auth.json` 含登录态 cookie，勿提交到 git。

## 变量自定义

所有平台/人员/流程/仓库变量集中在 `rdc-config.yaml`（见 `config.example.yaml` 注释）：
`base_url / workspace / project_id / team_id / tenant_id / api_key / assignee_emp_no / assignee_name /
team_name / work_item_type / task_type / status_flow / initial_status / wic_base_url /
wic_version / work_item_type_key / state_field_id / chrome_debug_port / chrome_profile_dir /
browser / chrome_path / auth_wait_seconds / auth_max_age_hours / file_url_hosts / git_author / repos /
excel_columns / auth_file`。其中 `excel_columns` 仅支持在平台标准列内增删/排序（生成与导入均以标准列集为准，非标准列会报错或被忽略）。

## 目录结构

```
rdc-work-items/
├── SKILL.md                # 本文件（精简入口）
├── manifest.json           # 元数据：名称/版本/依赖（零 pip）/结构
├── config.example.yaml     # 配置模板
├── references/             # workflow / architecture / api 详细指引
├── scripts/                # 核心实现（纯标准库）
│   ├── rdc_workflow        # 入口
│   └── rdc/                # ws / net / yamlio / xlsx / api / auth / doctor / ...
├── examples/rdc-sample/    # 离线示例：work_items.json → 工作量 Excel
└── tests/                  # 可运行验证（python3 tests/run_all.py）
```

详细月度操作步骤与常见问题见 `references/workflow.md`。
