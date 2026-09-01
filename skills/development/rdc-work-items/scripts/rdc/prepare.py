# -*- coding: utf-8 -*-
"""Excel 处理：生成导入文件 / 提取编号。

纯标准库：xlsx 由内置 xlsx.py（zipfile+XML）读写，不依赖 openpyxl。
状态流转不再走 Excel 导入（见 api.update_work_items_state）。
"""
from . import xlsx

HEADER_ORDER = ["编号", "标题", "工作项类型", "状态", "指派给", "更新时间",
                "计划开始时间", "实际完成时间", "初始估计", "创建人", "创建时间",
                "团队", "详细说明", "任务类型"]


def _read_rows(path):
    header, rows = xlsx.read_table(path)
    if not rows:
        raise ValueError(f"{path} 无数据")
    return header, rows


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
            "编号": r[id_i] if 0 <= id_i < len(r) else "",
            "标题": r[title_i] if 0 <= title_i < len(r) else "",
            "状态": r[state_i] if 0 <= state_i < len(r) else "",
        })
    return out


def collect_ids(path):
    """读取文件中「编号」列的工作项编号列表（用于 updateWorkItems 状态流转）。"""
    header, rows = _read_rows(path)
    if "编号" not in header:
        raise ValueError(f"{path} 没有「编号」列")
    id_i = header.index("编号")
    ids = []
    for r in rows:
        if not any(r):
            continue
        v = r[id_i] if id_i < len(r) else ""
        if v not in (None, ""):
            ids.append(str(v))
    return ids


def prepare(src, out, status="新建", keep_ids=False, keep_updated_time=False):
    """把源文件（导出结果格式）转换为导入文件。

    - 默认：状态改为指定值（新建），清空编号（创建新工作项），移除更新时间列
    - --keep-ids：保留编号（用于更新已有工作项）
    - --keep-updated-time：保留更新时间列（平台会告警但可导入）
    """
    header, rows = _read_rows(src)
    cols = {h: i for i, h in enumerate(header)}

    # 仅保留在标准导出结果中的列
    keep = [h for h in HEADER_ORDER if h in cols]
    if not keep_updated_time:
        for drop in ("更新时间", "创建人", "创建时间"):
            if drop in keep:
                keep.remove(drop)

    out_rows = []
    for r in rows:
        if not any(r):
            continue
        row = []
        for h in keep:
            val = r[cols[h]] if h in cols else None
            if h == "状态":
                val = status
            if h == "编号" and not keep_ids:
                val = ""
            row.append(val)
        out_rows.append(row)

    widths = {chr(65 + j): (90 if h == "详细说明" else 22) for j, h in enumerate(keep)}
    xlsx.write_table(out, keep, out_rows, sheet_name="导出结果", widths=widths)
    return {"items": len(out_rows), "status": status, "columns": keep, "out": out}
