# -*- coding: utf-8 -*-
"""研发云工作项接口封装：check-excel / importExcel / export excel / updateWorkItems（纯标准库）。"""
import os
import urllib.parse
from dataclasses import dataclass, field

from . import net

MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DEFAULT_WIC_BASE = "https://www.srdcloud.cn/zte-plm-wic-api"
# 平台返回的下载地址（fileUrl）主机白名单：点开头表示后缀匹配。
# 防止响应被污染时把会话 Cookie 外带或经 file:// 读取本地文件（可经配置 file_url_hosts 扩展）。
DEFAULT_FILE_URL_HOSTS = (".srdcloud.cn",)


def _file_url_hosts(cfg=None):
    hosts = (cfg or {}).get("file_url_hosts") or DEFAULT_FILE_URL_HOSTS
    if isinstance(hosts, str):
        hosts = [h.strip() for h in hosts.split(",") if h.strip()]
    return tuple(hosts)


def assert_safe_file_url(url, hosts=DEFAULT_FILE_URL_HOSTS):
    """校验下载地址：仅 https 且主机匹配白名单，否则拒绝（不发起请求、不附带 Cookie）。"""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise RdcError(f"下载地址非 https，已拒绝：{url[:80]}")
    host = (parsed.hostname or "").lower()
    ok = False
    for h in hosts:
        base = str(h).strip().lstrip(".").lower()
        if not base:
            continue
        if host == base or host.endswith("." + base):
            ok = True
            break
    if not ok:
        raise RdcError(f"下载地址主机 {host or '(空)'} 不在白名单内，已拒绝")
    return url


class RdcError(Exception):
    pass


@dataclass
class ValidateResult:
    """check-excel 校验结果：message 为平台 successMsg/errMsg 摘要，raw 保留原始 bo。"""
    message: str = ""
    raw: dict = field(default_factory=dict)


@dataclass
class ImportResult:
    """importExcel 结果：ids 为成功创建的工作项编号，raw 保留原始 taskInfo/bo。"""
    ids: list = field(default_factory=list)
    succeeded: int = 0
    failed: int = 0
    report_url: str = ""
    raw: dict = field(default_factory=dict)


@dataclass
class ExportResult:
    """导出结果：saved/bytes 为本地文件信息，total 为平台总条数（可能为 None），raw_task 保留任务信息。"""
    saved: str = ""
    bytes: int = 0
    total: object = None
    raw_task: dict = field(default_factory=dict)


@dataclass
class UpdateResult:
    """updateWorkItems 结果：succeeded/failed 为已规范化列表，raw 保留原始 bo。"""
    succeeded: list = field(default_factory=list)
    failed: list = field(default_factory=list)
    raw: dict = field(default_factory=dict)


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
    """导入数据校验（check-excel），只读安全。返回 ValidateResult。"""
    with open(file_path, "rb") as f:
        content = f.read()
    files = {"file": (os.path.basename(file_path), content, MIME_XLSX)}
    url = f"{cfg['base_url']}/wim/workspaces/{cfg['workspace']}/work_items/check-excel"
    data = _check_code(net.post_multipart(url, _headers(cfg, auth), files=files, timeout=120))
    bo = data.get("bo", {}) or {}
    return ValidateResult(message=str(bo.get("successMsg") or bo.get("errMsg") or ""), raw=bo)


def import_items(cfg, auth, file_path, team_id=None):
    """导入工作项（importExcel）。team_id 缺省用配置。返回 ImportResult。"""
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
    bo = data.get("bo", {}) or {}
    task = bo.get("taskInfo") or bo
    ids = import_ids(task)
    return ImportResult(ids=ids,
                        succeeded=int(task.get("succeededItemsSize", len(ids)) or 0),
                        failed=int(task.get("failedItemsSize", 0) or 0),
                        report_url=str(task.get("fileUrl", "") or ""),
                        raw=task)


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
    assert_safe_file_url(file_url, _file_url_hosts(cfg))
    content = net.get_bytes(file_url, headers={"Cookie": auth.get("cookie_header", "")}, timeout=300)
    import os as _os
    d = _os.path.dirname(_os.path.abspath(out_path))
    if d:
        _os.makedirs(d, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(content)
    return ExportResult(saved=out_path, bytes=len(content),
                        total=task.get("totalSize"), raw_task=task)


def download(url, auth=None, headers=None, cfg=None):
    """下载平台文件，返回内容。默认仅允许 https + file_url_hosts 白名单主机。"""
    assert_safe_file_url(url, _file_url_hosts(cfg))
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
        # 与 body workItems[].workItemTypeKey 保持一致（原页面快照硬编码 Fault，与 Task 不一致）
        "workItemTypeKey": cfg.get("work_item_type_key", "Task"),
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
    bo = data.get("bo", {}) or {}
    return UpdateResult(succeeded=list(bo.get("succeededItems", []) or []),
                        failed=list(bo.get("failedItems", []) or []), raw=bo)
