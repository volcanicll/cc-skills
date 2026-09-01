# -*- coding: utf-8 -*-
"""export_body（导出请求体）测试：python3 tests/test_export.py

对齐研发云页面实际导出报文（2026-09 实测成功报文）：
workItemTypeKeys=[]、crossWorkspaceKeyMapping.filter=[]、
selectItems 8 列、sortItems 按 System_ChangedDate 倒序、System_CreatedDate 过滤。
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from rdc import api

CFG = {
    "workspace": "P22CQQYYF0016",
    "team_id": "bdv_33380",
    "tenant_id": "20001",
    "assignee_emp_no": "srd17347933525",
    "assignee_name": "向灿",
}


def test_export_body_aligns_page_payload():
    body = api.export_body(CFG, since="2026-09-01", until="2026-09-02")

    assert body["appCode"] == "WicDefault"
    assert body["conditions"] == ["System_WorkspaceKey='P22CQQYYF0016'"]
    assert body["crossWorkspaceKeyMapping"] == {"filter": []}
    assert body["workItemTypeKeys"] == []
    assert body["sortItems"] == [{"isAscending": False, "key": "System_ChangedDate"}]
    assert body["viewName"] == "P22CQQYYF0016AllWorkItems"
    assert body["workspaceKey"] == "P22CQQYYF0016"
    assert body["queryCategory"] == "latest"

    # selectItems 与页面报文一致（8 列，工作项类型在前）
    assert [s["key"] for s in body["selectItems"]] == [
        "System_WorkItemType", "System_Id", "System_Title", "System_State",
        "System_AppointedTo", "System_ChangedDate", "OriginalEstimate",
        "DXYJY_ActualFinishDate",
    ]

    # filterItems：指派给 + 状态 + 标签 + 迭代 + 创建时间(between)
    fid = [f["filterId"] for f in body["filterItems"]]
    assert fid == ["System_AppointedTo", "System_State", "System_Tag",
                   "IterationPath", "System_CreatedDate"]
    created = body["filterItems"][-1]
    assert created["data"] == '["2026-09-01","2026-09-02"]'
    assert created["filterValue"] == "2026-09-01,2026-09-02"
    assert created["operator"] == "between"

    appoint = body["filterItems"][0]
    assert appoint["filterValue"] == "srd17347933525"
    # data 是 JSON 字符串，解析后含 label
    data = json.loads(appoint["data"])
    assert data[0]["label"] == "向灿 srd17347933525"
    assert data[0]["value"] == "srd17347933525"
    assert data[0]["name"] == "向灿"


def test_export_body_no_date_filter():
    body = api.export_body(CFG)
    fid = [f["filterId"] for f in body["filterItems"]]
    assert "System_CreatedDate" not in fid
    assert body["filterItems"][0]["filterValue"] == "srd17347933525"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("export tests passed")
