# -*- coding: utf-8 -*-
"""doctor（环境自检）测试：python3 tests/test_doctor.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from rdc import doctor


def test_doctor_flags_missing_config():
    cfg = {"workspace": "YOUR_WORKSPACE", "project_id": "", "team_id": "T",
           "tenant_id": "20001", "api_key": "k", "assignee_emp_no": "e",
           "assignee_name": "n", "team_name": "t", "git_author": "a",
           "repos": [], "auth_max_age_hours": 12}
    ok, lines = doctor.run(cfg, auth_path=os.path.join(tempfile.mkdtemp(), "auth.json"))
    assert ok is False
    assert any("工作区" in l and "❌" in l for l in lines)
    assert any("项目 ID" in l and "❌" in l for l in lines)


def test_doctor_warns_but_ok_on_missing_auth():
    cfg = {"workspace": "W", "project_id": "P", "team_id": "T",
           "tenant_id": "20001", "api_key": "k", "assignee_emp_no": "e",
           "assignee_name": "n", "team_name": "t", "git_author": "a",
           "repos": [], "auth_max_age_hours": 12,
           "chrome_profile_dir": ""}
    ok, lines = doctor.run(cfg, auth_path=os.path.join(tempfile.mkdtemp(), "auth.json"))
    assert ok is True  # 无阻断性问题，仅告警
    assert any("登录信息" in l and "⚠" in l for l in lines)
    assert any("repos" in l and "⚠" in l for l in lines)


def test_doctor_stale_auth_warns():
    tmp = tempfile.mkdtemp(prefix="rdc-doctor-")
    auth_path = os.path.join(tmp, "auth.json")
    with open(auth_path, "w", encoding="utf-8") as f:
        import json
        json.dump({"fetched_at": "2020-01-01 00:00:00", "source": "cdp",
                   "headers": {"x-api-key": "k", "x-auth-value": "v",
                               "x-emp-no": "e", "x-tenant-id": "20001"}}, f)
    cfg = {"workspace": "W", "project_id": "P", "team_id": "T", "tenant_id": "20001",
           "api_key": "k", "assignee_emp_no": "e", "assignee_name": "n",
           "team_name": "t", "git_author": "a", "repos": [],
           "auth_max_age_hours": 12, "chrome_profile_dir": ""}
    ok, lines = doctor.run(cfg, auth_path=auth_path)
    assert any("已过期" in l for l in lines)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("doctor tests passed")
