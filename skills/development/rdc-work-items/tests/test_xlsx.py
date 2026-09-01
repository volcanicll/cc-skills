# -*- coding: utf-8 -*-
"""xlsx（纯标准库读写）测试：python3 tests/test_xlsx.py"""
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "rdc"))

import xlsx

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def _roundtrip(headers, rows, widths=None):
    out = os.path.join(tempfile.mkdtemp(), "t.xlsx")
    xlsx.write_table(out, headers, rows, widths=widths)
    return xlsx.read_table(out)


def test_roundtrip_basic():
    headers = ["编号", "标题", "初始估计", "详细说明"]
    rows = [
        ["", "前端开发-登录", "8", "完成登录模块"],
        ["P22CQQYYF0016-6864", "工作助手", 16, "含换行\n第二行"],
        [None, "布尔", "8", ""],
        [True, "布尔列", 8.5, "x"],
    ]
    h, r = _roundtrip(headers, rows, widths={"A": 24, "B": 46, "C": 12})
    assert h == headers
    assert r[0] == ["", "前端开发-登录", "8", "完成登录模块"]
    assert r[1] == ["P22CQQYYF0016-6864", "工作助手", 16, "含换行\n第二行"]
    assert r[2] == ["", "布尔", "8", ""]
    assert r[3][0] is True and r[3][2] == 8.5


def test_xml_escaping():
    h, r = _roundtrip(["标题"], [['a<b>&"c" 中文']])
    assert r[0][0] == 'a<b>&"c" 中文'


def test_read_shared_strings_and_types():
    """模拟平台导出的 sharedStrings 格式文件。"""
    shared = ["编号", "标题", "状态", "P22CQQYYF0016-6864", "登录", "已完成"]
    ss_xml = ('<?xml version="1.0"?><sst xmlns="%s" count="6" uniqueCount="6">' % MAIN +
              "".join(f"<si><t>{s}</t></si>" for s in shared) + "</sst>")
    sheet_xml = ('<?xml version="1.0"?><worksheet xmlns="%s"><sheetData>' % MAIN +
                 '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c>'
                 '<c r="C1" t="s"><v>2</v></c></row>'
                 '<row r="2"><c r="A2" t="s"><v>3</v></c>'
                 '<c r="B2" t="inlineStr"><is><t>登录模块</t></is></c>'
                 '<c r="C2" t="s"><v>5</v></c></row>'
                 '<row r="3"><c r="A3" t="s"><v>3</v></c><c r="B3" t="s"><v>4</v></c>'
                 '<c r="C3"><v>1</v></c></row>'
                 '<row r="4"><c r="A4" t="b"><v>1</v></c><c r="B4" t="str"><v>公式值</v></c>'
                 '<c r="C4"><v>45890.5</v></c></row>'
                 "</sheetData></worksheet>")
    wb_xml = ('<?xml version="1.0"?><workbook xmlns="%s" '
              'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
              '<sheets><sheet name="导出结果" sheetId="1" r:id="rId1"/></sheets></workbook>' % MAIN)
    rels_xml = ('<?xml version="1.0"?><Relationships '
                'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                'Target="worksheets/sheet1.xml"/></Relationships>')
    path = os.path.join(tempfile.mkdtemp(), "export.xlsx")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>')
        z.writestr("xl/workbook.xml", wb_xml)
        z.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        z.writestr("xl/sharedStrings.xml", ss_xml)
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    h, r = xlsx.read_table(path)
    assert h == ["编号", "标题", "状态"]
    assert r[0] == ["P22CQQYYF0016-6864", "登录模块", "已完成"]
    assert r[1] == ["P22CQQYYF0016-6864", "登录", 1]
    assert r[2][0] is True and r[2][1] == "公式值" and r[2][2] == 45890.5


def test_rich_text_shared_string():
    shared = [{"parts": ["编号", "标题"]}]
    # 富文本 <si><r><t>..</t></r><r><t>..</t></r></si>
    ss_xml = ('<?xml version="1.0"?><sst xmlns="%s" count="2" uniqueCount="2">'
              "<si><r><t>编</t></r><r><t>号</t></r></si>"
              "<si><r><t>标</t></r><r><t>题</t></r></si></sst>" % MAIN)
    sheet_xml = ('<?xml version="1.0"?><worksheet xmlns="%s"><sheetData>'
                 '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>'
                 "</sheetData></worksheet>" % MAIN)
    wb_xml = ('<?xml version="1.0"?><workbook xmlns="%s" '
              'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
              '<sheets><sheet name="S" sheetId="1" r:id="rId1"/></sheets></workbook>' % MAIN)
    rels_xml = ('<?xml version="1.0"?><Relationships '
                'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                'Target="worksheets/sheet1.xml"/></Relationships>')
    path = os.path.join(tempfile.mkdtemp(), "rich.xlsx")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>')
        z.writestr("xl/workbook.xml", wb_xml)
        z.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        z.writestr("xl/sharedStrings.xml", ss_xml)
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    h, _ = xlsx.read_table(path)
    assert h == ["编号", "标题"], h


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("xlsx tests passed")
