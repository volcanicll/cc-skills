# 月度工作量录入完整流程

## 准备（一次性）

1. 复制 `config.example.yaml` → `config.yaml`，按环境修改：
   - `workspace/project_id/team_id/tenant_id/api_key`：平台参数（可在浏览器 Network 抓取核对）
   - `assignee_emp_no/assignee_name/team_name`：指派人信息
   - `status_flow`：平台实际工作流状态（默认 新建→处理中→已完成→已关闭）
   - `repos`：本机 git 仓库列表；`git_author`：要统计的作者
2. 启动 Chrome（保留登录态）并打开研发云工作项页：
   - macOS：`/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222`
   - Windows：`start chrome --remote-debugging-port=9222`（或对 chrome.exe 快捷方式加该参数）
   - 也可用 Edge（`--remote-debugging-port=9222`），脚本自动探测两者
3. 提取鉴权：`python3 scripts/rdc_workflow --config config.yaml auth`
   （Windows 用 `py -3 scripts\rdc_workflow --config config.yaml auth`）
   - 依赖 `websocket-client requests pyyaml openpyxl`：`pip3 install --user websocket-client requests pyyaml openpyxl`
   - 工具通过 CDP 直连浏览器级 WebSocket（`suppress_origin`，静默，无需用户操作）

## 每月流程

### 1. 统计提交
```bash
python3 scripts/rdc_workflow --config config.yaml stats \
  --since 2026-08-01 --until 2026-08-31 -o commits.json
```
输出每个仓库的业务提交（自动过滤 merge/test/dist/chore/stash 等噪音）。AI 按模块/功能人工分组为工作项。

### 2. 生成工作量 Excel
`work_items.json` 格式：
```json
{"work_items": [{"title": "前端开发-资金归集-登录：…", "hours": 8,
                 "start": "2026-08-01", "end": "2026-08-05", "description": "…"}]}
```
```bash
python3 scripts/rdc_workflow --config config.yaml build-excel -i work_items.json -o 营销域8月-示例.xlsx
```

### 3. 导入（创建）
```bash
python3 scripts/rdc_workflow --config config.yaml prepare 营销域8月-示例.xlsx -o 导入-新建.xlsx --status 新建
python3 scripts/rdc_workflow --config config.yaml validate 导入-新建.xlsx   # 应显示"预计新增 N 条"
python3 scripts/rdc_workflow --config config.yaml import 导入-新建.xlsx     # 平台创建并生成编号
```

### 4. 导出（拿到真实编号）
```bash
python3 scripts/rdc_workflow --config config.yaml export -o 导出.xlsx \
  --since 2026-08-01 --until 2026-08-31
```

### 5. 状态流转（逐级）
```bash
for st in 处理中 已完成 已关闭; do
  python3 scripts/rdc_workflow --config config.yaml set-status 导出.xlsx -o 导入-$st.xlsx --status $st
  python3 scripts/rdc_workflow --config config.yaml validate 导入-$st.xlsx   # "预计更新 N 条"
  python3 scripts/rdc_workflow --config config.yaml import 导入-$st.xlsx
  python3 scripts/rdc_workflow --config config.yaml export -o 导出.xlsx --since ... --until ...  # 刷新
done
```
或直接用 `flow --src … --out-dir flow --yes` 一条命令完成（内部含校验与失败中断）。

### 6. 月度绩效自评
基于工作项/工时生成 100 字以内自评，要点：主导模块、完成功能、保障交付。

## 常见问题

| 现象 | 原因 / 处理 |
|---|---|
| 导入报"工作流不存在" | 状态名错误或跳级。核对 `status_flow` 与实际平台状态，逐级流转 |
| 校验提示"列选项不能包含…" | 平台不支持导入该列（更新时间/创建人/创建时间），prepare 已默认移除 |
| 导入 `failedItemsSize>0` | 工具自动下载错误报告查看具体原因；常见为单据被修改，重新导出最新文件再导入 |
| `check-excel` 显示"更新"而非"新增" | 文件含编号=更新已有项；创建新项需编号为空 |
| CDP 连接 403 | 使用 suppress_origin（工具已内置）；勿用 agent-browser 自带的 Origin 头连接 |
| Chrome 未开调试端口 | 用 `--remote-debugging-port=9222` 重启 Chrome（保留原用户目录与登录态） |
| 鉴权过期 | 重新运行 `auth`（自动从页面提取最新 cookie/token） |
