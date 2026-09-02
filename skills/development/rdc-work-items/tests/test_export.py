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
    "workspace": "P22TEST0000001",
    "team_id": "test_team_001",
    "tenant_id": "20001",
    "assignee_emp_no": "srd10000000000",
    "assignee_name": "张三",
}


def test_export_body_aligns_page_payload():
    body = api.export_body(CFG, since="2026-09-01", until="2026-09-02")

    assert body["appCode"] == "WicDefault"
    assert body["conditions"] == ["System_WorkspaceKey='P22TEST0000001'"]
    assert body["crossWorkspaceKeyMapping"] == {"filter": []}
    assert body["workItemTypeKeys"] == []
    assert body["sortItems"] == [{"isAscending": False, "key": "System_ChangedDate"}]
    assert body["viewName"] == "P22TEST0000001AllWorkItems"
    assert body["workspaceKey"] == "P22TEST0000001"
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
    assert appoint["filterValue"] == "srd10000000000"
    # data 是 JSON 字符串，解析后含 label
    data = json.loads(appoint["data"])
    assert data[0]["label"] == "张三 srd10000000000"
    assert data[0]["value"] == "srd10000000000"
    assert data[0]["name"] == "张三"


def test_export_body_no_date_filter():
    body = api.export_body(CFG)
    fid = [f["filterId"] for f in body["filterItems"]]
    assert "System_CreatedDate" not in fid
    assert "DXYJY_PlanStartDate" not in fid
    assert body["filterItems"][0]["filterValue"] == "srd10000000000"


def test_export_body_plan_start_filter():
    """计划开始时间（DXYJY_PlanStartDate）单独过滤，字段形状对齐平台页面报文。"""
    body = api.export_body(CFG, plan_since="2026-07-31", plan_until="2026-08-14")
    fid = [f["filterId"] for f in body["filterItems"]]
    assert "System_CreatedDate" not in fid
    assert fid[-1] == "DXYJY_PlanStartDate"
    plan = body["filterItems"][-1]
    assert plan["operator"] == "between"
    assert plan["data"] == '["2026-07-31","2026-08-14"]'
    assert plan["filterValue"] == "2026-07-31,2026-08-14"
    assert plan["hidden"] is False


def test_export_body_plan_start_plus_created():
    """创建时间与计划开始时间可叠加过滤，计划开始时间排在其后。"""
    body = api.export_body(CFG, since="2026-09-01", until="2026-09-02",
                           plan_since="2026-07-31", plan_until="2026-08-14")
    fid = [f["filterId"] for f in body["filterItems"]]
    assert fid[-2:] == ["System_CreatedDate", "DXYJY_PlanStartDate"]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("export tests passed")
