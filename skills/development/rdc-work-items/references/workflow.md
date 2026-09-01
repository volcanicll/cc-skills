# 月度工作量录入完整流程

## 环境要求（零 pip 依赖）

- Python 3.9+（仅标准库，无需 `pip install`）
- Chrome / Edge（以 `--remote-debugging-port` 启动且已登录 srdcloud.cn）
- git（本机已克隆待统计仓库）

## 准备（一次性）

1. 首次配置（交互向导）：`python3 scripts/rdc_workflow setup-config`
   - 输入 `workspace/project_id/team_id/tenant_id/api_key`（平台参数）、
     `assignee_emp_no/assignee_name/team_name`（指派人）、`git_author`（git 作者）
   - 写入全局配置 `~/.config/rdc-work-items.yaml`（Windows `%APPDATA%\rdc-work-items.yaml`），
     之后所有命令自动加载，无需 `--config`
   - 非交互方式：`setup-config --no-input --workspace … --api-key … --repos …`
   - 可选：复制 `config.example.yaml` → 本地 `config.yaml` 覆盖（优先级高于全局）
   - `status_flow` / `wic_base_url` 等默认即可；如需调整见 `config.example.yaml` 注释
2. 启动 Chrome（保留登录态）并打开研发云工作项页：
   - macOS：`/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222`
   - Windows：`start chrome --remote-debugging-port=9222`（或对 chrome.exe 快捷方式加该参数）
   - 也可用 Edge；脚本自动探测 `DevToolsActivePort` 或 HTTP 探测调试端口
3. 提取鉴权（无需任何 pip 包）：
   ```bash
   python3 scripts/rdc_workflow --config config.yaml auth
   ```
   （Windows 用 `py -3 scripts\rdc_workflow --config config.yaml auth`）

## 每月流程

### 1. 统计提交
```bash
python3 scripts/rdc_workflow --config config.yaml stats \
  --since 2026-08-01 --until 2026-08-31 -o commits.json
```
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
python3 scripts/rdc_workflow --config config.yaml build-excel -i work_items.json -o 营销域8月-示例.xlsx
```

### 3. 导入（创建）
```bash
python3 scripts/rdc_workflow --config config.yaml prepare 营销域8月-示例.xlsx -o 导入-新建.xlsx --status 新建
python3 scripts/rdc_workflow --config config.yaml validate 导入-新建.xlsx   # 应显示"预计新增 N 条"
python3 scripts/rdc_workflow --config config.yaml import 导入-新建.xlsx     # 平台创建并返回编号
```

### 4. 状态流转（接口方式，不再走 Excel 导入）
创建后从导入响应提取工作项编号（`bo.taskInfo.succeededItems[].data["1"]`），
用 `update-status` 逐级调用 `updateWorkItems/edit` 接口：

```bash
# 从含编号的导出/导入文件读取编号并流转
python3 scripts/rdc_workflow --config config.yaml update-status 导出.xlsx --status 处理中
# 或直接指定编号
python3 scripts/rdc_workflow --config config.yaml update-status --ids P22CQQYYF0016-6864,P22CQQYYF0016-6865 --status 已完成
```

逐级执行：`处理中 → 已完成 → 已关闭`（按 `status_flow`，不可跳级）。

### 5. 全流程（一步到位）
```bash
python3 scripts/rdc_workflow --config config.yaml flow --src 营销域8月-示例.xlsx --out-dir flow --yes
```
内部：prepare → validate → import（创建）→ 从响应提取编号 → 接口逐级流转。
默认 dry-run（只校验不导入），加 `--yes` 才真正执行。

### 6. 导出（可选，用于月度记录）
```bash
python3 scripts/rdc_workflow --config config.yaml export -o 导出.xlsx \
  --since 2026-08-01 --until 2026-08-31
```

### 7. 月度绩效自评
基于工作项/工时生成 100 字以内自评，要点：主导模块、完成功能、保障交付。

## 常见问题

| 现象 | 原因 / 处理 |
|---|---|
| 导入报"工作流不存在" | 状态名错误或跳级。核对 `status_flow` 与实际平台状态，逐级流转 |
| 校验提示"列选项不能包含…" | 平台不支持导入该列（更新时间/创建人/创建时间），prepare 已默认移除 |
| 导入 `failedItemsSize>0` | 工具自动下载错误报告查看具体原因；常见为单据被修改，重新导出最新文件再导入 |
| `update-status` 返回 failedItems | 编号错误 / 状态非法 / 跳级；核对编号与 `status_flow` |
| `check-excel` 显示"更新"而非"新增" | 文件含编号=更新已有项；创建新项需编号为空 |
| CDP 连接 403 | 使用 suppress_origin（工具已内置）；勿用 agent-browser 自带的 Origin 头连接 |
| Chrome 未开调试端口 | 用 `--remote-debugging-port=9222` 重启 Chrome（保留原用户目录与登录态） |
| 鉴权过期 | 重新运行 `auth`（自动从页面提取最新 cookie/token） |
| 提示找不到模块 `websocket` 等 | 本工具已零依赖，无需安装；如残留旧脚本请用本版本 scripts/ |
