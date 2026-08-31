# -*- coding: utf-8 -*-
"""Excel 处理：生成导入文件 / 修改状态列。"""
import shutil

import openpyxl
from openpyxl.styles import Alignment

HEADER_ORDER = ["编号", "标题", "工作项类型", "状态", "指派给", "更新时间",
                "计划开始时间", "实际完成时间", "初始估计", "创建人", "创建时间",
                "团队", "详细说明", "任务类型"]


def _read_rows(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError(f"{path} 无数据")
    header = [str(h).strip() if h is not None else "" for h in rows[0]]
    return header, rows[1:]


def summarize(path):
    """打印文件中的工作项：编号、标题、状态。"""
    header, rows = _read_rows(path)
    idx = {h: i for i, h in enumerate(header)}
    id_i, title_i, state_i = idx.get("编号", -1), idx.get("标题", -1), idx.get("状态", -1)
    out = []
    for r in rows:
        if not any(r):
            continue
        out.append({
            "编号": r[id_i] if id_i >= 0 else "",
            "标题": r[title_i] if title_i >= 0 else "",
            "状态": r[state_i] if state_i >= 0 else "",
        })
    return out


def prepare(src, out, status="新建", keep_ids=False, keep_updated_time=False):
    """把源文件（导出结果格式）转换为导入文件。

    - 默认：状态改为指定值（新建），清空编号（创建新工作项），移除更新时间列
    - --keep-ids：保留编号（用于更新已有工作项，如状态流转）
    - --keep-updated-time：保留更新时间列（平台会告警但可导入）
    """
    wb = openpyxl.load_workbook(src)
    ws = wb.active
    header = [str(c.value).strip() if c.value is not None else "" for c in ws[1]]
    cols = {h: i for i, h in enumerate(header)}

    # 仅保留在标准导出结果中的列
    keep = [h for h in HEADER_ORDER if h in cols]
    if not keep_updated_time:
        for drop in ("更新时间", "创建人", "创建时间"):
            if drop in keep:
                keep.remove(drop)

    # 新表
    nwb = openpyxl.Workbook()
    nws = nwb.active
    nws.title = "导出结果"
    for j, h in enumerate(keep, start=1):
        c = nws.cell(row=1, column=j, value=h)
        c.font = openpyxl.styles.Font(name="宋体", size=14, bold=True)
        c.fill = openpyxl.styles.PatternFill(patternType="solid", fgColor="D9D9D9")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = openpyxl.styles.Border(
            left=openpyxl.styles.Side(style="thin"), right=openpyxl.styles.Side(style="thin"),
            top=openpyxl.styles.Side(style="thin"), bottom=openpyxl.styles.Side(style="thin"))

    n = 0
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not any(r):
            continue
        n += 1
        for j, h in enumerate(keep, start=1):
            val = r[cols[h]] if h in cols else None
            if h == "状态":
                val = status
            if h == "编号" and not keep_ids:
                val = ""
            c = nws.cell(row=n + 1, column=j, value=val)
            c.alignment = Alignment(vertical="center", wrap_text=True)

    # 列宽
    for j, h in enumerate(keep, start=1):
        nws.column_dimensions[openpyxl.utils.get_column_letter(j)].width = 90 if h == "详细说明" else 22
    nwb.save(out)
    return {"items": n, "status": status, "columns": keep, "out": out}


def set_status(src, out, status):
    """修改文件中的状态列（用于状态流转后重新导入）。"""
    shutil.copy(src, out)
    wb = openpyxl.load_workbook(out)
    ws = wb.active
    header = [str(c.value).strip() if c.value is not None else "" for c in ws[1]]
    if "状态" not in header:
        raise ValueError("文件中没有「状态」列")
    si = header.index("状态")
    changed = 0
    for row in ws.iter_rows(min_row=2):
        if row[si].row and any(c.value not in (None, "") for c in row):
            row[si].value = status
            changed += 1
    wb.save(out)
    return {"changed": changed, "status": status, "out": out}
