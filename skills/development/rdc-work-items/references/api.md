# 研发云接口说明

## 基础地址

| 用途 | 地址 |
| --- | --- |
| 导入/导出/校验 | `{base_url}`（默认 `https://www.srdcloud.cn/zte-rdcloud-rdc-wimbackend`） |
| 状态流转 | `{wic_base_url}`（默认 `https://www.srdcloud.cn/zte-plm-wic-api`） |

## 鉴权头（auth 提取）

`x-api-key / x-auth-value / x-emp-no / x-lang-id / x-tenant-id / x-device /
x-frame-origin / x-project-id`，另附 `Cookie` 头。
状态流转额外需要 `x-wic-version`（默认 `V1.24.22`，可在配置覆盖）。

## 接口

### 1. 校验导入文件（只读）

```
POST {base_url}/wim/workspaces/{workspace}/work_items/check-excel
Content-Type: multipart/form-data
file: <xlsx>
```
返回 `bo`（预计新增/更新条数）。

### 2. 导入工作项

```
POST {base_url}/wim/workspaces/{workspace}/work_items/importExcel
Content-Type: multipart/form-data
importHtmlField: true
teamId: {team_id}
importBlankField: true
file: <xlsx>
```
成功返回 `bo.taskInfo`，其中：
```
succeededItems[].data = {"1": "P22CQQYYF0016-6864"}   # 工作项编号
succeededItemsSize / failedItemsSize / fileUrl(错误报告)
```

### 3. 导出工作项 Excel

```
POST {base_url}/wim/workItem/workspaces/{workspace}/export/excel?flap=false
Content-Type: application/json
body: filterItems(指派给/状态/计划开始时间等) + selectItems + ...
```
异步返回 `bo.taskInfo.fileUrl`，再 GET 下载。

### 4. 状态流转（updateWorkItems，PUT）

```
PUT {wic_base_url}/api/workspaces/{workspace}/work_items/updateWorkItems/edit
Content-Type: application/json
x-wic-version: V1.24.22

{
  "workItems": [
    {"id": "P22CQQYYF0016-6864", "workItemTypeKey": "Task", "workspaceKey": "P22CQQYYF0016"}
  ],
  "fields": [
    {"fieldObj": {…System_State 字段元数据…}, "key": "System_State", "name": "状态",
     "value": "已完成", "multiValue": false, "modifyType": "replace", "type": "state"}
  ]
}
```
响应：
```
code.code == "0000" 成功
bo.succeededItems[] 更新成功；bo.failedItems[] 失败项
```
注意事项：
- 状态必须按 `status_flow` **逐级**流转，跳级或状态名错误报"工作流不存在"。
- `fieldObj` 为页面同款完整字段对象（id/workspaceKey 参数化），
  必要时可在配置覆盖 `state_field_id`。

## 常见问题

| 现象 | 处理 |
| --- | --- |
| `code.code != 0000` | 按 msg 定位；鉴权过期先重新 `auth` |
| 更新返回 failedItems | 检查编号是否正确、状态是否合法、是否跳级 |
| 导入 failedItemsSize>0 | 下载 `fileUrl` 错误报告查看原因 |
| 校验提示列不支持 | 平台不支持导入该列，`prepare` 已默认移除 |
