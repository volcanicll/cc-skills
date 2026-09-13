# -*- coding: utf-8 -*-
"""Excel 处理：生成导入文件 / 提取编号。

纯标准库：xlsx 由内置 xlsx.py（zipfile+XML）读写，不依赖 openpyxl。
状态流转不再走 Excel 导入（见 api.update_work_items_state）。
"""
from . import schema, xlsx

# 与 rdc/schema.py 保持同源（单一事实源），勿单独手抄
HEADER_ORDER = list(schema.EXPORT_COLUMNS)


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
    missing = [h for h in HEADER_ORDER if h not in cols]
    dropped_unknown = [h for h in header if h not in HEADER_ORDER]
    warnings = []
    if missing:
        warnings.append(
            f"源文件缺少标准列：{', '.join(missing)}（已忽略，确认是否为平台导出格式）")
    if dropped_unknown:
        warnings.append(
            f"源文件含非标准列，将被忽略：{', '.join(dropped_unknown)}"
            "（导入路径仅支持平台标准列，如确需新增请先在平台确认可导入）")
    if not keep_updated_time:
        for drop in schema.IMPORT_UNSUPPORTED:
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

    widths = {xlsx.col_letter(j + 1): (90 if h == "详细说明" else 22) for j, h in enumerate(keep)}
    xlsx.write_table(out, keep, out_rows, sheet_name="导出结果", widths=widths)
    return {"items": len(out_rows), "status": status, "columns": keep,
            "warnings": warnings, "out": out}


def needs_import_prep(path):
    """判断「导出结果」文件是否需要自动转为可导入文件（用于创建新项）。

    规则：文件含平台不支持列（更新时间/创建人/创建时间）且「编号」列全空时返回 True——
    即 build-excel 生成的工作量 Excel 或平台导出后尚未创建的行，import 可直接自动转换；
    已含编号（更新已有项）或已不含不支持列（已 prepare 过）的文件返回 False，保持原样导入。
    """
    try:
        header, rows = _read_rows(path)
    except FileNotFoundError:
        return False  # 文件不存在等留待后续导入环节报出明确错误
    if not any(c in header for c in schema.IMPORT_UNSUPPORTED):
        return False
    if "编号" not in header:
        return False
    id_i = header.index("编号")
    for r in rows:
        if not any(r):
            continue
        v = r[id_i] if id_i < len(r) else ""
        if str(v).strip():
            return False  # 含编号 → 更新已有项，不自动转换
    return True


def strip_unsupported(src, out, status=None):
    """把「导出结果」文件转为可导入文件：只移除平台不支持列与非标准列。

    与 prepare() 的区别：保留编号与状态等列的原值（status 传入时才改写状态），
    适合 import 对创建型文件（编号为空）的自动转换；也可用于更新前的轻量清理
    （此时编号会被保留，配合平台逐行判断新增/更新）。
    返回 {"items", "status", "columns", "warnings", "out"}。
    """
    header, rows = _read_rows(src)
    cols = {h: i for i, h in enumerate(header)}
    keep = [h for h in HEADER_ORDER
            if h in cols and h not in schema.IMPORT_UNSUPPORTED]
    missing = [h for h in HEADER_ORDER if h not in cols]
    dropped_unknown = [h for h in header if h not in HEADER_ORDER]
    warnings = []
    if missing:
        warnings.append(
            f"源文件缺少标准列：{', '.join(missing)}（已忽略，确认是否为平台导出格式）")
    if dropped_unknown:
        warnings.append(
            f"源文件含非标准列，将被忽略：{', '.join(dropped_unknown)}"
            "（导入路径仅支持平台标准列，如确需新增请先在平台确认可导入）")

    out_rows = []
    for r in rows:
        if not any(r):
            continue
        row = []
        for h in keep:
            val = r[cols[h]] if h in cols else None
            if status is not None and h == "状态":
                val = status
            row.append(val)
        out_rows.append(row)

    widths = {xlsx.col_letter(j + 1): (90 if h == "详细说明" else 22) for j, h in enumerate(keep)}
    xlsx.write_table(out, keep, out_rows, sheet_name="导出结果", widths=widths)
    return {"items": len(out_rows), "status": status, "columns": keep,
            "warnings": warnings, "out": out}
