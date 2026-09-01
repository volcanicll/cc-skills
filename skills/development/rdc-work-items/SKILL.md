---
name: rdc-work-items
description: 研发云（srdcloud.cn）工作项月度工作量全流程自动化：从 git 提交统计生成工作量 Excel，通过 CDP 获取登录态鉴权后调用平台接口完成工作项导入、导出与状态流转（新建→处理中→已完成→已关闭）。纯 Python 标准库、零 pip 依赖。所有环境变量（工作区/团队/指派人/状态流/仓库列表等）通过 config.yaml 自定义。用于"工作量统计/生成工作量excel/导入导出工作项/月度绩效"等请求。
metadata:
  short-description: 研发云工作项导入导出与状态流转自动化
---

# 研发云工作项自动化（rdc-work-items）

按"统计工作量 → 生成 Excel → 导入平台 → 接口逐级流转状态"的月度流程，调用研发云接口完成录入，
避免手工上传下载。脚本位于 `scripts/`，全部变量由 `config.yaml` 自定义。
**纯 Python 标准库，零 pip 依赖**（WebSocket/HTTP/YAML/Excel 均内置实现）。

## 平台要求

- **操作系统**：macOS / Windows / Linux 均可（Python 脚本跨平台）。
- **运行环境**：Python 3.9+，**无需安装任何第三方包**（标准库即可）。
- **浏览器**：Chrome 或 Edge，需以 `--remote-debugging-port` 启动并已登录 srdcloud.cn。
- **Windows**：用 `py -3 scripts\rdc_workflow`（或 `scripts/rdc_workflow.cmd`）代替 `python3 scripts/rdc_workflow`；
  在 `config.yaml` 的 `chrome_profile_dir` 填 Windows 用户数据目录；
  留空时脚本自动按系统探测 Chrome/Edge 的 `DevToolsActivePort` 或 HTTP 探测调试端口。
- **git**：统计提交需要本机已克隆对应仓库，仓库路径在 `config.yaml` 的 `repos` 中配置。

## 快速开始

1. 准备配置：复制 `config.example.yaml` 为 `config.yaml`，修改工作区/团队/指派人/状态流/仓库列表等变量。
2. 获取鉴权（Chrome 需带 `--remote-debugging-port=9222` 启动且已登录 srdcloud.cn）：
   ```bash
   python3 scripts/rdc_workflow --config config.yaml auth
   ```
3. 统计提交（按配置的 `git_author` 过滤噪音）：
   ```bash
   python3 scripts/rdc_workflow --config config.yaml stats --since 2026-08-01 --until 2026-08-31 -o commits.json
   ```
4. AI 将 `commits.json` 的提交按模块/功能分组为工作项（标题/工时/起止日期/说明），写入 `work_items.json`，
   再生成工作量 Excel：
   ```bash
   python3 scripts/rdc_workflow --config config.yaml build-excel -i work_items.json -o 营销域8月-示例.xlsx
   ```
5. 全流程（默认 dry-run 只校验，加 `--yes` 才真实执行）：
   ```bash
   python3 scripts/rdc_workflow --config config.yaml flow --src 营销域8月-示例.xlsx --out-dir flow --yes
   ```
   或分步执行（创建走 Excel 导入，状态流转走接口）：
   ```bash
   ... prepare --status 新建 && validate && import      # 创建，响应返回工作项编号
   ... update-status 导出.xlsx --status 处理中          # 接口流转（也可 --ids 指定编号）
   ... update-status 导出.xlsx --status 已完成
   ... update-status 导出.xlsx --status 已关闭
   ```

## 关键规则（安全）

- **编号为空 = 创建新工作项；编号有值 = 更新已有工作项**。切勿重复导入"新建"文件（会重复创建）。
- **状态必须按配置的 `status_flow` 逐级流转**（默认 新建→处理中→已完成→已关闭），
  通过 `updateWorkItems/edit` 接口调用，跳级或状态名错误会报"工作流不存在"。
- **创建**：每个 `import` 前先 `validate`，确认"预计新增/更新 N 条"与预期一致；
  导入返回 `failedItemsSize>0` 时下载错误报告（`fileUrl`）查看原因。
- **状态流转**：`update-status` 从导入响应（`succeededItems[].data["1"]`）或含编号的
  Excel 读取工作项编号，调用接口逐级流转；返回 `failedItems` 时核对编号与状态。
- `auth.json` 含登录态 cookie，勿提交到 git。

## 变量自定义

所有平台/人员/流程/仓库变量集中在 `config.yaml`（见 `config.example.yaml` 注释）：
`base_url / workspace / project_id / team_id / tenant_id / api_key / assignee_emp_no / assignee_name /
team_name / domain / work_item_type / task_type / status_flow / initial_status / wic_base_url /
wic_version / work_item_type_key / state_field_id / chrome_debug_port / chrome_profile_dir /
git_author / repos / excel_columns / auth_file`。

## 目录结构

```
rdc-work-items/
├── SKILL.md                # 本文件（精简入口）
├── manifest.json           # 元数据：名称/版本/依赖（零 pip）/结构
├── config.example.yaml     # 配置模板
├── references/             # workflow / architecture / api 详细指引
├── scripts/                # 核心实现（纯标准库）
│   ├── rdc_workflow        # 入口
│   └── rdc/                # ws / net / yamlio / xlsx / api / auth / ...
├── examples/rdc-sample/    # 离线示例：work_items.json → 工作量 Excel
└── tests/                  # 可运行验证（python3 tests/run_all.py）
```

详细月度操作步骤与常见问题见 `references/workflow.md`。
