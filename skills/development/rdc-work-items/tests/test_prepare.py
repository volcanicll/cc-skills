# -*- coding: utf-8 -*-
"""prepare（导入文件转换）测试：python3 tests/test_prepare.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from rdc import prepare, xlsx


def _make_src(columns, rows):
    path = os.path.join(tempfile.mkdtemp(prefix="rdc-prep-"), "src.xlsx")
    xlsx.write_table(path, columns, rows, sheet_name="导出结果")
    return path


def test_prepare_missing_columns_warns():
    # 源文件缺「更新时间」等标准列
    src = _make_src(["编号", "标题", "状态", "指派给"],
                    [["", "工作项A", "新建", "张三 srd10000000000"]])
    r = prepare.prepare(src, os.path.join(os.path.dirname(src), "out.xlsx"), status="新建")
    assert r["warnings"], "缺少标准列应产生警告"
    assert any("缺少标准列" in w for w in r["warnings"])
    assert "更新时间" not in r["columns"]


def test_prepare_full_columns_no_warning():
    cols = ["编号", "标题", "工作项类型", "状态", "指派给", "更新时间", "计划开始时间",
            "实际完成时间", "初始估计", "创建人", "创建时间", "团队", "详细说明", "任务类型"]
    src = _make_src(cols, [["", "工作项A", "任务", "新建", "张三 srd10000000000",
                            "", "", "", "8", "", "", "团队A", "说明", "开发"]])
    r = prepare.prepare(src, os.path.join(os.path.dirname(src), "out.xlsx"), status="新建")
    assert r["warnings"] == []
    assert "编号" in r["columns"] and "更新时间" not in r["columns"]


def test_prepare_drops_unknown_columns_with_warning():
    """源文件含非标准列时：警告并丢弃，不静默带入导入文件。"""
    cols = ["编号", "标题", "状态", "领域", "昵称"]
    src = _make_src(cols, [["", "工作项A", "新建", "前端", "昵称A"]])
    r = prepare.prepare(src, os.path.join(os.path.dirname(src), "out.xlsx"), status="新建")
    assert any("非标准列" in w for w in r["warnings"])
    assert "领域" not in r["columns"] and "昵称" not in r["columns"]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("prepare tests passed")
