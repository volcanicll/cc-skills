# -*- coding: utf-8 -*-
"""excelgen（工时范围校验 + 生成）测试：python3 tests/test_excelgen.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from rdc import excelgen

CFG = {"initial_status": "新建", "work_item_type": "任务", "task_type": "开发",
       "assignee_name": "张三", "assignee_emp_no": "srd10000000000",
       "team_name": "T"}


def _items(hours):
    return [{"title": "工作项A", "hours": hours, "start": "2026-08-01",
             "end": "2026-08-02", "description": "d"}]


def test_hours_boundaries():
    excelgen.validate_items(_items(1))
    excelgen.validate_items(_items(24))
    excelgen.validate_items(_items(8))
    excelgen.validate_items(_items("16"))  # 字符串数字也接受


def test_hours_out_of_range():
    for bad in (0, 0.5, 24.5, 25, -1):
        try:
            excelgen.validate_items(_items(bad))
            raise AssertionError(f"hours={bad} 应被拒绝")
        except ValueError as e:
            assert "超出范围" in str(e)


def test_hours_missing_or_invalid():
    try:
        excelgen.validate_items([{"title": "x", "start": "2026-08-01"}])
        raise AssertionError("缺 hours 应报错")
    except ValueError as e:
        assert "缺失或非数字" in str(e)
    try:
        excelgen.validate_items([{"title": "x", "hours": "abc"}])
        raise AssertionError("非数字 hours 应报错")
    except ValueError as e:
        assert "缺失或非数字" in str(e)


def test_build_rejects_out_of_range():
    out = os.path.join(tempfile.mkdtemp(), "x.xlsx")
    try:
        excelgen.build(CFG, _items(30), out)
        raise AssertionError("越界工时生成应报错")
    except ValueError as e:
        assert "超出范围" in str(e)
        assert not os.path.exists(out)


def test_build_ok():
    out = os.path.join(tempfile.mkdtemp(), "ok.xlsx")
    r = excelgen.build(CFG, _items(8), out)
    assert r["items"] == 1 and os.path.exists(out)


def test_custom_unknown_column_rejected():
    """excel_columns 含非标准列时应在生成前报错，且不产生文件。"""
    from rdc import schema
    out = os.path.join(tempfile.mkdtemp(), "bad.xlsx")
    cfg = dict(CFG, excel_columns=["编号", "标题", "领域"])
    try:
        excelgen.build(cfg, _items(8), out)
        raise AssertionError("非标准列应报错")
    except ValueError as e:
        assert "非标准列" in str(e)
        assert not os.path.exists(out)
    assert "领域" not in schema.EXPORT_COLUMNS


def test_custom_subset_columns_ok():
    """excel_columns 在标准列内取子集/排序应正常生成。"""
    out = os.path.join(tempfile.mkdtemp(), "sub.xlsx")
    cfg = dict(CFG, excel_columns=["标题", "状态", "初始估计"])
    r = excelgen.build(cfg, _items(8), out)
    assert r["items"] == 1
    from rdc import xlsx
    headers, rows = xlsx.read_table(out)
    assert headers == ["标题", "状态", "初始估计"], headers
    assert rows[0][0] == "工作项A" and rows[0][2] == "8"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("excelgen tests passed")
