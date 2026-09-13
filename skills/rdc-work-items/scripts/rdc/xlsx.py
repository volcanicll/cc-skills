# -*- coding: utf-8 -*-
"""极简 xlsx 读写（纯标准库 zipfile + XML，替代 openpyxl）。

写入：inlineStr 单元格 + 基础样式（表头宋体加粗灰底、细边框、居中等）。
读取：支持 sharedStrings / inlineStr / str / number / boolean，
      足够覆盖平台导出文件与本地生成文件。
"""
import re
import zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"

_NUM_RE = re.compile(r"[-+]?(\d+\.?\d*|\.\d+)$")
# 单个 zip 成员解压大小上限（64MB），防恶意/损坏 xlsx 拖垮内存
MAX_MEMBER_BYTES = 64 * 1024 * 1024


def _read_member(z, name):
    try:
        info = z.getinfo(name)
    except KeyError:
        raise ValueError(f"xlsx 缺少成员 {name}") from None
    if info.file_size > MAX_MEMBER_BYTES:
        raise ValueError(f"xlsx 成员 {name} 解压后过大（{info.file_size} 字节），已拒绝解析")
    return z.read(name)


def _q(tag):
    return "{" + NS_MAIN + "}" + tag


def _col_index(ref):
    m = re.match(r"([A-Z]+)", ref or "")
    if not m:
        return 1
    n = 0
    for ch in m.group(1):
        n = n * 26 + (ord(ch) - 64)
    return n


def _cell_ref(col, row):
    s = ""
    c = col
    while c:
        c, r = divmod(c - 1, 26)
        s = chr(65 + r) + s
    return f"{s}{row}"


# ---------------------------------------------------------------------------
# 写入
# ---------------------------------------------------------------------------

def _cell_xml(ref, value, style):
    if value is None:
        value = ""
    if isinstance(value, bool):
        inner = f'<v>{"1" if value else "0"}</v>'
        t = ' t="b"'
    elif isinstance(value, (int, float)):
        inner = f"<v>{value}</v>"
        t = ' t="n"'
    else:
        inner = f"<is><t xml:space=\"preserve\">{escape(str(value))}</t></is>"
        t = ' t="inlineStr"'
    return f'<c r="{ref}"{t} s="{style}">{inner}</c>'


def write_table(out_path, headers, rows, sheet_name="导出结果", widths=None):
    """生成最小 xlsx。rows 为数据行（不含表头），widths 为 {列字母: 宽度} 或列表。"""
    if isinstance(widths, (list, tuple)):
        widths = {_cell_ref(i + 1, 1)[0]: w for i, w in enumerate(widths)}

    cols_xml = ""
    if widths:
        parts = []
        for letter in sorted(widths, key=_col_index):
            parts.append(f'<col min="{_col_index(letter)}" max="{_col_index(letter)}" '
                         f'width="{widths[letter]}" customWidth="1"/>')
        cols_xml = "<cols>" + "".join(parts) + "</cols>"

    ncol = max(len(headers), max((len(r) for r in rows), default=0))
    sheet_parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                   f'<worksheet xmlns="{NS_MAIN}">{cols_xml}<sheetData>']
    hcells = [f'<c r="{_cell_ref(i, 1)}" t="inlineStr" s="1">'
              f'<is><t xml:space="preserve">{escape(str(h))}</t></is></c>'
              for i, h in enumerate(headers, start=1)]
    sheet_parts.append(f'<row r="1">{"".join(hcells)}</row>')
    for ri, row in enumerate(rows, start=2):
        cells = []
        for ci in range(ncol):
            val = row[ci] if ci < len(row) else ""
            cells.append(_cell_xml(_cell_ref(ci + 1, ri), val, 2))
        sheet_parts.append(f'<row r="{ri}">{"".join(cells)}</row>')
    sheet_parts.append("</sheetData></worksheet>")
    sheet_xml = "".join(sheet_parts)

    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<styleSheet xmlns="{NS_MAIN}">'
        '<fonts count="2">'
        '<font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><sz val="14"/><name val="宋体"/></font>'
        '</fonts>'
        '<fills count="2">'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFD9D9D9"/>'
        '<bgColor indexed="64"/></patternFill></fill>'
        '</fills>'
        '<borders count="2">'
        '<border><left/><right/><top/><bottom/><diagonal/></border>'
        '<border><left style="thin"/><right style="thin"/><top style="thin"/>'
        '<bottom style="thin"/><diagonal/></border>'
        '</borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="3">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="1" borderId="1" xfId="0" '
        'applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">'
        '<alignment horizontal="center" vertical="center" wrapText="1"/></xf>'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" '
        'applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>'
        '</cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        '</styleSheet>'
    )

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Types xmlns="{NS_CT}">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '</Types>'
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{NS_PKG_REL}">'
        f'<Relationship Id="rId1" Type="{NS_REL}/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{NS_PKG_REL}">'
        f'<Relationship Id="rId1" Type="{NS_REL}/worksheet" Target="worksheets/sheet1.xml"/>'
        f'<Relationship Id="rId2" Type="{NS_REL}/styles" Target="styles.xml"/>'
        '</Relationships>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<workbook xmlns="{NS_MAIN}" xmlns:r="{NS_REL}">'
        f'<sheets><sheet name="{escape(sheet_name)}" sheetId="1" r:id="rId1"/></sheets>'
        '</workbook>'
    )

    import os
    d = os.path.dirname(os.path.abspath(out_path))
    if d:
        os.makedirs(d, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        z.writestr("xl/styles.xml", styles_xml)
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return out_path


# ---------------------------------------------------------------------------
# 读取
# ---------------------------------------------------------------------------

def _read_shared_strings(z):
    shared = []
    if "xl/sharedStrings.xml" not in z.namelist():
        return shared
    root = ET.fromstring(_read_member(z, "xl/sharedStrings.xml"))
    for si in root.iter(_q("si")):
        shared.append("".join(t.text or "" for t in si.iter(_q("t"))))
    return shared


def _first_sheet_path(z):
    try:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
    except KeyError:
        return "xl/worksheets/sheet1.xml"
    sheet = wb.find(_q("sheets") + "/" + _q("sheet"))
    if sheet is None:
        return "xl/worksheets/sheet1.xml"
    rid = sheet.get("{" + NS_REL + "}id")
    target = None
    if rid:
        try:
            rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
            for rel in rels:
                if rel.get("Id") == rid:
                    target = rel.get("Target")
                    break
        except KeyError:
            pass
    if not target:
        return "xl/worksheets/sheet1.xml"
    if target.startswith("/"):
        return target.lstrip("/")
    return "xl/" + target


def _cell_value(c, shared):
    t = c.get("t")
    v = c.find(_q("v"))
    if t == "inlineStr":
        is_ = c.find(_q("is"))
        if is_ is None:
            return ""
        return "".join(x.text or "" for x in is_.iter(_q("t")))
    if t == "s":
        try:
            idx = int(v.text or "0") if v is not None else 0
        except ValueError:
            return ""  # 损坏/异常共享字符串索引 → 按空值处理，不崩溃
        return shared[idx] if idx < len(shared) else ""
    if t == "str":
        return v.text or "" if v is not None else ""
    if t == "b":
        return (v.text or "0") == "1" if v is not None else False
    if v is None:
        return ""
    raw = v.text or ""
    if _NUM_RE.fullmatch(raw):
        try:
            return int(raw) if "." not in raw else float(raw)
        except ValueError:
            return raw
    return raw


def read_table(path):
    """读取 xlsx 首个工作表，返回 (headers, rows)。headers 为表头字符串列表。"""
    with zipfile.ZipFile(path) as z:
        shared = _read_shared_strings(z)
        sheet_path = _first_sheet_path(z)
        root = ET.fromstring(_read_member(z, sheet_path))
        headers, rows = None, []
        for row in root.iter(_q("row")):
            values = {}
            max_col = 0
            for c in row.findall(_q("c")):
                col = _col_index(c.get("r")) - 1
                values[col] = _cell_value(c, shared)
                max_col = max(max_col, col + 1)
            if not values:
                continue
            row_vals = [values.get(i, "") for i in range(max_col)]
            if headers is None:
                headers = [str(x).strip() if x is not None else "" for x in row_vals]
            else:
                rows.append(row_vals)
    return headers or [], rows
