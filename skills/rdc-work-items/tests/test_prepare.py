# -*- coding: utf-8 -*-
"""prepare（导入文件转换）测试：python3 tests/test_prepare.py"""
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from rdc import prepare, schema, xlsx

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"


def _make_src(columns, rows):
    path = os.path.join(tempfile.mkdtemp(prefix="rdc-prep-"), "src.xlsx")
    xlsx.write_table(path, columns, rows, sheet_name="导出结果")
    return path


def _make_platform_export(rows):
    """按平台导出风格构造 xlsx：标准 14 列 + sharedStrings + 首行表头。

    覆盖真实导出文件的形态（sharedStrings 去重、第一行为表头、无横幅/合并单元格），
    用于钉住 prepare/summarize/collect_ids 对平台导出文件的读取契约。
    """
    headers = list(schema.EXPORT_COLUMNS)
    seen, table, sid = {}, [], {}

    def _sid(v):
        s = "" if v is None else str(v)
        if s not in seen:
            seen[s] = len(table)
            table.append(s)
        return seen[s]

    def _row_xml(r, row_idx):
        cells = []
        for ci in range(len(headers)):
            v = r[ci] if ci < len(r) else ""
            col = xlsx.col_letter(ci + 1)
            cells.append(f'<c r="{col}{row_idx}" t="s"><v>{_sid(v)}</v></c>')
        return f'<row r="{row_idx}">{"".join(cells)}</row>'

    rows_xml = [_row_xml(headers, 1)]
    for i, r in enumerate(rows, start=2):
        rows_xml.append(_row_xml(r, i))
    ss_xml = ('<?xml version="1.0"?><sst xmlns="%s" count="%d" uniqueCount="%d">'
              % (MAIN, len(table), len(table))
              + "".join(f"<si><t>{t}</t></si>" for t in table) + "</sst>")
    sheet_xml = ('<?xml version="1.0"?><worksheet xmlns="%s"><sheetData>'
                 % MAIN + "".join(rows_xml) + "</sheetData></worksheet>")
    wb_xml = ('<?xml version="1.0"?><workbook xmlns="%s" '
              'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
              '<sheets><sheet name="导出结果" sheetId="1" r:id="rId1"/></sheets></workbook>' % MAIN)
    rels_xml = ('<?xml version="1.0"?><Relationships xmlns="%s">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                'Target="worksheets/sheet1.xml"/></Relationships>' % REL)
    path = os.path.join(tempfile.mkdtemp(prefix="rdc-export-"), "export.xlsx")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("_rels/.rels", '<Relationships xmlns="%s"/>' % REL)
        z.writestr("xl/workbook.xml", wb_xml)
        z.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        z.writestr("xl/sharedStrings.xml", ss_xml)
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)
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


def test_platform_export_contract():
    """平台导出文件（sharedStrings、标准 14 列）经 prepare/summarize/collect_ids 全链路契约。"""
    base = ["", "前端开发-资金归集-登录", "任务", "新建", "张三 srd10000000000",
            "2026-08-01 10:00:00", "2026-08-01 09:00:00", "2026-08-01 18:00:00",
            "8", "张三 srd10000000000", "2026-08-01 09:00:00", "资金团队", "完成登录模块", "开发"]
    rows = [
        list(base),
        list(base),  # 第二个工作项：带编号
        list(base),
    ]
    rows[1][0] = "P22TEST0000001-6864"
    rows[1][1] = "前端开发-资金归集-对账"
    rows[2][0] = "P22TEST0000001-6865"
    rows[2][1] = "前端开发-资金归集-报表"
    src = _make_platform_export(rows)

    # collect_ids：只取编号列非空
    assert prepare.collect_ids(src) == ["P22TEST0000001-6864", "P22TEST0000001-6865"]
    # summarize：3 条，含新建项
    items = prepare.summarize(src)
    assert len(items) == 3
    assert items[0]["编号"] == "" and items[1]["编号"] == "P22TEST0000001-6864"
    # prepare：无警告，输出列为标准列去掉导入不支持的三列（更新时间/创建人/创建时间）
    out = os.path.join(os.path.dirname(src), "out.xlsx")
    r = prepare.prepare(src, out, status="新建")
    assert r["warnings"] == [], r["warnings"]
    assert len(r["columns"]) == len(schema.EXPORT_COLUMNS) - len(schema.IMPORT_UNSUPPORTED)
    assert "编号" in r["columns"] and "更新时间" not in r["columns"]
    assert r["items"] == 3


def test_needs_import_prep_build_excel_output():
    """build-excel 输出（编号全空 + 含不支持列）应判定为需要自动转导入文件。"""
    from rdc import excelgen
    cols = list(schema.EXPORT_COLUMNS)
    rows = [["", "工作项A", "任务", "新建", "张三 srd10000000000", "", "",
             "", "8", "", "", "团队A", "说明", "开发"]]
    src = _make_src(cols, rows)
    assert prepare.needs_import_prep(src) is True
    # 同一文件经 excelgen 生成也应命中
    out = os.path.join(tempfile.mkdtemp(prefix="rdc-gen-"), "gen.xlsx")
    excelgen.build({"initial_status": "新建", "work_item_type": "任务", "task_type": "开发",
                    "assignee_name": "张三", "assignee_emp_no": "srd10000000000",
                    "team_name": "团队A"}, [{"title": "工作项A", "hours": 8}], out)
    assert prepare.needs_import_prep(out) is True


def test_needs_import_prep_false_for_prepared_or_ids():
    """已 prepare（无不支持列）或含编号（更新已有项）的文件不应自动转换。"""
    # 已 prepare：不支持列已移除
    cols = ["编号", "标题", "工作项类型", "状态", "指派给", "计划开始时间",
            "实际完成时间", "初始估计", "团队", "详细说明", "任务类型"]
    src = _make_src(cols, [["", "工作项A", "任务", "新建", "张三 srd10000000000",
                            "", "", "8", "团队A", "说明"]])
    assert prepare.needs_import_prep(src) is False
    # 平台导出：含编号 → 更新，不自动转换
    full = list(schema.EXPORT_COLUMNS)
    exp = _make_src(full, [["P22TEST0000001-6864", "工作项A", "任务", "处理中",
                            "张三 srd10000000000", "2026-08-01 10:00:00", "", "", "8",
                            "张三 srd10000000000", "2026-08-01 09:00:00", "团队A", "说明", "开发"]])
    assert prepare.needs_import_prep(exp) is False


def test_strip_unsupported_keeps_state_and_ids():
    """strip_unsupported：只移除不支持列与非标准列，保留编号/状态等原值。"""
    cols = list(schema.EXPORT_COLUMNS) + ["领域"]
    rows = [
        ["P22TEST0000001-6864", "工作项A", "任务", "处理中", "张三 srd10000000000",
         "2026-08-01 10:00:00", "", "", "8", "张三 srd10000000000",
         "2026-08-01 09:00:00", "团队A", "说明", "开发", "前端"],
    ]
    src = _make_src(cols, rows)
    out = os.path.join(os.path.dirname(src), "stripped.xlsx")
    r = prepare.strip_unsupported(src, out)
    assert any("非标准列" in w for w in r["warnings"])
    header, out_rows = xlsx.read_table(out)
    assert "更新时间" not in header and "创建人" not in header and "领域" not in header
    assert "编号" in header and "状态" in header
    it = prepare.summarize(out)[0]
    assert it["编号"] == "P22TEST0000001-6864"  # 编号保留（更新语义由调用方决定）
    assert it["状态"] == "处理中"  # 状态未被强制改写


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("prepare tests passed")
