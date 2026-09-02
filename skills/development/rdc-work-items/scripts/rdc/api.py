# -*- coding: utf-8 -*-
"""研发云工作项接口封装：check-excel / importExcel / export excel / updateWorkItems（纯标准库）。"""
import os

from . import net

MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DEFAULT_WIC_BASE = "https://www.srdcloud.cn/zte-plm-wic-api"


class RdcError(Exception):
    pass


def _headers(cfg, auth, extra=None):
    h = dict(auth.get("headers", {}))
    h.setdefault("Accept", "application/json, text/plain, */*")
    if extra:
        h.update(extra)
    return h


def _check_code(data):
    code = data.get("code", {})
    if isinstance(code, dict) and code.get("code") != "0000":
        raise RdcError(f"平台错误: {code}")
    return data


def validate(cfg, auth, file_path):
    """导入数据校验（check-excel），只读安全。返回 bo。"""
    with open(file_path, "rb") as f:
        content = f.read()
    files = {"file": (os.path.basename(file_path), content, MIME_XLSX)}
    url = f"{cfg['base_url']}/wim/workspaces/{cfg['workspace']}/work_items/check-excel"
    data = _check_code(net.post_multipart(url, _headers(cfg, auth), files=files, timeout=120))
    return data.get("bo", {})


def import_items(cfg, auth, file_path, team_id=None):
    """导入工作项（importExcel）。team_id 缺省用配置。返回 taskInfo。"""
    team_id = team_id or cfg.get("team_id") or ""
    with open(file_path, "rb") as f:
        content = f.read()
    fields = {
        "importHtmlField": "true",
        "teamId": team_id,
        "importBlankField": "true",
    }
    files = {"file": (os.path.basename(file_path), content, MIME_XLSX)}
    url = f"{cfg['base_url']}/wim/workspaces/{cfg['workspace']}/work_items/importExcel"
    data = _check_code(net.post_multipart(url, _headers(cfg, auth), fields=fields, files=files, timeout=300))
    bo = data.get("bo", {})
    return bo.get("taskInfo", bo)


def import_ids(bo):
    """从 importExcel 响应 bo 提取成功创建的工作项编号列表。

    平台返回形如：taskInfo.succeededItems[].data = {"1": "P22TEST0000001-6864"}
    """
    task = bo.get("taskInfo") or bo
    ids = []
    for item in task.get("succeededItems", []):
        data = item.get("data") or {}
        if isinstance(data, dict):
            for v in data.values():
                if v:
                    ids.append(str(v))
        elif data:
            ids.append(str(data))
    return ids


def export_body(cfg, since=None, until=None, assignee=None, state="@all",
               page_size=200, select_items=None):
    """构造导出请求体（与研发云页面实际报文一致，2026-09 实测）。"""
    assignee = assignee or cfg.get("assignee_emp_no")
    assignee_name = cfg.get("assignee_name", "")
    filters = [
        {
            "data": f'[{{"label":"{assignee_name} {assignee}","value":"{assignee}","name":"{assignee_name}","checked":false,"headUrl":""}}]'
            if assignee else "[]",
            "filterId": "System_AppointedTo", "operator": "in",
            "filterValue": assignee or "@all", "hidden": False,
        },
        {"data": "", "filterId": "System_State", "operator": "in",
         "filterValue": state, "hidden": False},
        {"data": "", "filterId": "System_Tag", "operator": "in",
         "filterValue": "@all", "hidden": False},
        {"data": "", "filterId": "IterationPath", "operator": "in",
         "filterValue": "@all", "hidden": False},
    ]
    if since and until:
        filters.append({
            "data": f'["{since}","{until}"]', "filterId": "System_CreatedDate",
            "operator": "between", "filterValue": f"{since},{until}", "hidden": False,
        })

    select_items = select_items or [
        {"key": "System_WorkItemType", "width": ""},
        {"key": "System_Id", "width": ""},
        {"key": "System_Title", "width": ""},
        {"key": "System_State", "width": ""},
        {"key": "System_AppointedTo", "width": ""},
        {"key": "System_ChangedDate", "width": ""},
        {"key": "OriginalEstimate", "width": ""},
        {"key": "DXYJY_ActualFinishDate", "width": ""},
    ]
    return {
        "appCode": "WicDefault",
        "conditions": [f"System_WorkspaceKey='{cfg['workspace']}'"],
        "createFrom": "", "crossWorkspace": False, "crossWorkspaceAccessList": [],
        "crossWorkspaceKeyMapping": {"filter": []}, "disable": False,
        "filterItems": filters, "flowManager": True,
        "id": "6385a3ef0b13ba5558b937da", "inputFilterItems": [],
        "lastUpdateBy": "", "queryDraftFilter": "noDraft", "queryType": "filter",
        "resultType": "flat", "scrollId": "", "selectItems": select_items,
        "sortItems": [{"isAscending": False, "key": "System_ChangedDate"}],
        "teamId": cfg.get("team_id", ""), "tenantKey": cfg.get("tenant_id", "20001"),
        "userId": "systemAdmin", "viewBackupId": "",
        "viewName": f"{cfg['workspace']}AllWorkItems",
        "viewNameEn": f"{cfg['workspace']}AllWorkItems",
        "viewNameZh": f"{cfg['workspace']}AllWorkItems",
        "viewType": "public", "workItemTypeKeys": [],
        "workspaceKey": cfg["workspace"], "pageNo": 1, "pageSize": page_size,
        "appendParams": {}, "queryCondition": {"sourceClauses": []},
        "version": "2.0", "queryCategory": "latest",
    }


def export_excel(cfg, auth, out_path, since=None, until=None, assignee=None,
                 state="@all", page_size=200, team_id=None, select_items=None):
    """导出工作项 Excel（异步任务，返回 fileUrl 后下载）。"""
    body = export_body(cfg, since=since, until=until, assignee=assignee,
                       state=state, page_size=page_size, select_items=select_items)
    url = f"{cfg['base_url']}/wim/workItem/workspaces/{cfg['workspace']}/export/excel?flap=false"
    data = _check_code(net.request_json("POST", url, _headers(cfg, auth), payload=body, timeout=120))
    bo = data.get("bo", {})
    task = bo.get("taskInfo", {})
    file_url = task.get("fileUrl", "")
    if task.get("status") != "finish" and not file_url:
        raise RdcError(f"导出任务未完成：{task}")
    if not file_url:
        raise RdcError(f"导出未返回文件地址：{task}")
    content = net.get_bytes(file_url, headers={"Cookie": auth.get("cookie_header", "")}, timeout=300)
    import os as _os
    d = _os.path.dirname(_os.path.abspath(out_path))
    if d:
        _os.makedirs(d, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(content)
    return {"task": task, "saved": out_path, "bytes": len(content)}

def download(url, auth=None, headers=None):
    """下载平台文件，返回内容。"""
    h = headers or {}
    if auth and auth.get("cookie_header"):
        h["Cookie"] = auth["cookie_header"]
    content = net.get_bytes(url, headers=h, timeout=300)
    return {"content": content, "text": content.decode("utf-8", errors="replace")}


# ---------------------------------------------------------------------------
# 状态流转（updateWorkItems/edit 接口，不再走 Excel 导入）
# ---------------------------------------------------------------------------

def _state_field(cfg, status):
    """构造 fields[] 中 System_State 的完整字段对象（对齐平台页面请求体）。"""
    workspace = cfg["workspace"]
    field_id = cfg.get("state_field_id", "63f96af738aa624d3b708445")
    usage = {
        "controlType": "input",
        "customization": "system",
        "hidden": False,
        "hrefUrl": "",
        "key": "System_State",
        "label": "状态",
        "multiValue": False,
        "readonly": False,
        "referencePickListName": "",
        "remoteDataSource": "",
        "supportedOperations": [
            {"key": "eq", "value": "=", "wiqlOperator": "="},
            {"key": "neq", "value": "≠", "wiqlOperator": "!="},
            {"key": "was", "value": "was", "wiqlOperator": "was"},
        ],
        "workItemTypeKey": "Fault",
    }
    field_obj = {
        "calFormula": "",
        "canSortBy": True,
        "createTime": "2020-08-06T06:05:53.285+0000",
        "customization": "system",
        "description": "",
        "id": field_id,
        "key": "System_State",
        "name": "状态",
        "nameEn": "System_State",
        "nameZh": "状态",
        "remoteDataSource": "",
        "standardField": True,
        "type": "state",
        "unitName": "",
        "usages": [usage],
        "workspaceKey": workspace,
        "usage": usage,
        "value": "",
        "minValue": "",
        "maxValue": "",
        "datas": None,
        "operator": "in",
        "options": [],
        "hidden": False,
    }
    return {
        "fieldObj": field_obj,
        "key": "System_State",
        "name": "状态",
        "value": status,
        "multiValue": False,
        "modifyType": "replace",
        "type": "state",
    }


def update_work_items_state(cfg, auth, ids, status):
    """批量修改工作项状态（PUT updateWorkItems/edit）。ids 为工作项编号列表。"""
    if not ids:
        raise RdcError("没有可更新的工作项编号")
    workspace = cfg["workspace"]
    base = cfg.get("wic_base_url", DEFAULT_WIC_BASE)
    url = f"{base}/api/workspaces/{workspace}/work_items/updateWorkItems/edit"
    headers = _headers(cfg, auth, {
        "content-type": "application/json",
        "x-wic-version": cfg.get("wic_version", "V1.24.22"),
    })
    body = {
        "workItems": [
            {"id": str(i), "workItemTypeKey": cfg.get("work_item_type_key", "Task"),
             "workspaceKey": workspace}
            for i in ids
        ],
        "fields": [_state_field(cfg, status)],
    }
    data = _check_code(net.request_json("PUT", url, headers, payload=body, timeout=120))
    return data.get("bo", {})
