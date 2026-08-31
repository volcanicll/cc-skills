# -*- coding: utf-8 -*-
"""研发云工作项接口封装：check-excel / importExcel / export excel（配置驱动）。"""
import os

import requests

from . import config as _config


class RdcError(Exception):
    pass


def _headers(cfg, auth, extra=None):
    h = dict(auth.get("headers", {}))
    h.setdefault("Accept", "application/json, text/plain, */*")
    if extra:
        h.update(extra)
    return h


def _session(cfg, auth):
    s = requests.Session()
    s.headers.update(_headers(cfg, auth))
    cookie_header = auth.get("cookie_header")
    if cookie_header:
        s.headers["Cookie"] = cookie_header
    return s


def _check_code(resp):
    try:
        data = resp.json()
    except ValueError:
        raise RdcError(f"非 JSON 响应：HTTP {resp.status_code} {resp.text[:200]}")
    code = data.get("code", {})
    if code.get("code") != "0000":
        raise RdcError(f"平台错误: {code}")
    return data


def validate(cfg, auth, file_path):
    """导入数据校验（check-excel），只读安全。返回 bo。"""
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f,
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        url = f"{cfg['base_url']}/wim/workspaces/{cfg['workspace']}/work_items/check-excel"
        resp = _session(cfg, auth).post(url, files=files, timeout=120)
    return _check_code(resp).get("bo", {})


def import_items(cfg, auth, file_path, team_id=None):
    """导入工作项（importExcel）。team_id 缺省用配置。"""
    team_id = team_id or cfg.get("team_id") or ""
    with open(file_path, "rb") as f:
        data = {
            "file": (os.path.basename(file_path), f,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            "importHtmlField": (None, "true"),
            "teamId": (None, team_id),
            "importBlankField": (None, "true"),
        }
        url = f"{cfg['base_url']}/wim/workspaces/{cfg['workspace']}/work_items/importExcel"
        resp = _session(cfg, auth).post(url, files=data, timeout=300)
    bo = _check_code(resp).get("bo", {})
    return bo.get("taskInfo", bo)


def export_excel(cfg, auth, out_path, since=None, until=None, assignee=None,
                 state="@all", page_size=200, team_id=None, select_items=None):
    """导出工作项 Excel（异步任务，返回 fileUrl 后下载）。"""
    team_id = team_id or cfg.get("team_id") or ""
    assignee = assignee or cfg.get("assignee_emp_no")
    assignee_name = cfg.get("assignee_name", "")
    filters = [
        {
            "data": f'[{{"label":"{assignee_name} {assignee}","value":"{assignee}","name":"{assignee_name}","checked":false,"headUrl":""}}]'
            if assignee else "[]",
            "filterId": "System_AppointedTo", "operator": "in",
            "filterValue": assignee or "@all", "hidden": False,
        },
        {"data": "[]", "filterId": "System_State", "operator": "in",
         "filterValue": state, "hidden": False},
        {"data": "", "filterId": "System_Tag", "operator": "in",
         "filterValue": "@all", "hidden": False},
        {"data": "", "filterId": "IterationPath", "operator": "in",
         "filterValue": "@all", "hidden": False},
    ]
    if since and until:
        filters.append({
            "data": f'["{since}","{until}"]', "filterId": "DXYJY_PlanStartDate",
            "operator": "between", "filterValue": f"{since},{until}", "hidden": False,
        })
    else:
        filters.append({"data": "", "filterId": "DXYJY_PlanStartDate",
                        "operator": "between", "filterValue": "", "hidden": False})
    filters.append({"data": "", "filterId": "DXYJY_ActualFinishDate",
                    "operator": "between", "filterValue": "", "hidden": False})

    select_items = select_items or [
        {"key": "System_Id", "width": ""},
        {"key": "System_Title", "width": ""},
        {"key": "System_WorkItemType", "width": ""},
        {"key": "System_State", "width": ""},
        {"key": "System_AppointedTo", "width": ""},
        {"key": "System_ChangedDate", "width": ""},
        {"key": "DXYJY_PlanStartDate", "width": ""},
        {"key": "DXYJY_ActualFinishDate", "width": ""},
        {"key": "OriginalEstimate", "width": ""},
        {"key": "System_CreatedBy", "width": ""},
        {"key": "System_CreatedDate", "width": ""},
        {"key": "Team", "width": ""},
        {"key": "DXYJY_Detail_html", "width": ""},
        {"key": "srdcloud_PMC_renwuleixing", "width": ""},
    ]
    body = {
        "appCode": "WicDefault",
        "conditions": [f"System_WorkspaceKey='{cfg['workspace']}'"],
        "createFrom": "", "crossWorkspace": False, "crossWorkspaceAccessList": [],
        "crossWorkspaceKeyMapping": {"filter": ["任务"]}, "disable": False,
        "filterItems": filters, "flowManager": True,
        "id": "6385a3ef0b13ba5558b937da", "inputFilterItems": [],
        "lastUpdateBy": "", "queryDraftFilter": "noDraft", "queryType": "filter",
        "resultType": "flat", "scrollId": "", "selectItems": select_items,
        "sortItems": [{"isAscending": True, "key": "System_Title"}],
        "teamId": team_id, "tenantKey": cfg.get("tenant_id", "20001"),
        "userId": "systemAdmin", "viewBackupId": "",
        "viewName": f"{cfg['workspace']}AllWorkItems",
        "viewNameEn": f"{cfg['workspace']}AllWorkItems",
        "viewNameZh": f"{cfg['workspace']}AllWorkItems",
        "viewType": "public",
        "workItemTypeKeys": [f"Task:{cfg['workspace']}:任务"],
        "workspaceKey": cfg["workspace"], "pageNo": 1, "pageSize": page_size,
        "appendParams": {}, "queryCondition": {"sourceClauses": []},
        "version": "2.0", "queryCategory": "latest",
    }
    url = f"{cfg['base_url']}/wim/workItem/workspaces/{cfg['workspace']}/export/excel?flap=false"
    resp = _session(cfg, auth).post(url, json=body, timeout=120)
    bo = _check_code(resp).get("bo", {})
    task = bo.get("taskInfo", {})
    file_url = task.get("fileUrl", "")
    if task.get("status") != "finish" and not file_url:
        raise RdcError(f"导出任务未完成：{task}")
    if not file_url:
        raise RdcError(f"导出未返回文件地址：{task}")
    dl = requests.get(file_url, headers={"Cookie": auth.get("cookie_header", "")}, timeout=300)
    dl.raise_for_status()
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(dl.content)
    return {"task": task, "saved": out_path, "bytes": len(dl.content)}


def download(url, auth=None, headers=None):
    """下载平台文件，返回内容。"""
    h = headers or {}
    if auth and auth.get("cookie_header"):
        h["Cookie"] = auth["cookie_header"]
    r = requests.get(url, headers=h, timeout=300)
    r.raise_for_status()
    return {"content": r.content, "text": r.content.decode("utf-8", errors="replace")}
