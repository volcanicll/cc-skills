# -*- coding: utf-8 -*-
"""从工作项 JSON 生成工作量 Excel（导出结果格式，14 列）。

纯标准库：xlsx 由内置 xlsx.py（zipfile+XML）生成，不依赖 openpyxl。
"""
import json

from . import xlsx

# 单工作项工时范围（小时）：最小 1，最大不超过 24
MIN_HOURS = 1
MAX_HOURS = 24


def validate_items(items):
    """校验每个工作项工时在 [MIN_HOURS, MAX_HOURS] 区间，非法时抛出 ValueError。"""
    errors = []
    for it in items:
        title = it.get("title", "")
        raw = it.get("hours")
        try:
            hours = float(raw)
        except (TypeError, ValueError):
            errors.append(f"「{title}」hours 缺失或非数字: {raw!r}")
            continue
        if not (MIN_HOURS <= hours <= MAX_HOURS):
            errors.append(f"「{title}」hours={hours:g} 超出范围 [{MIN_HOURS}, {MAX_HOURS}]")
    if errors:
        raise ValueError("工作项工时校验失败（单工作项最小 1 小时、最大 24 小时）：\n"
                         + "\n".join(errors))
    return items


def build(cfg, items, out_path, status=None, updated_at=None, created_at=None):
    """items: [{"title","hours","start","end","description"}]
    生成 14 列「导出结果」格式工作簿。
    """
    validate_items(items)
    status = status or cfg.get("initial_status", "新建")
    updated_at = updated_at or ""
    created_at = created_at or ""
    columns = cfg.get("excel_columns", [
        "编号", "标题", "工作项类型", "状态", "指派给", "更新时间",
        "计划开始时间", "实际完成时间", "初始估计", "创建人", "创建时间",
        "团队", "详细说明", "任务类型"])

    rows = []
    for it in items:
        vals = {
            "编号": it.get("id", ""),
            "标题": it["title"],
            "工作项类型": cfg.get("work_item_type", "任务"),
            "状态": status,
            "指派给": f"{cfg.get('assignee_name','')}{cfg.get('assignee_emp_no','')}",
            "更新时间": updated_at,
            "计划开始时间": f"{it.get('start','')} 09:00:00" if it.get("start") else "",
            "实际完成时间": f"{it.get('end','')} 18:00:00" if it.get("end") else "",
            "初始估计": str(it.get("hours", "")),
            "创建人": f"{cfg.get('assignee_name','')}{cfg.get('assignee_emp_no','')}",
            "创建时间": created_at,
            "团队": cfg.get("team_name", ""),
            "详细说明": it.get("description", ""),
            "任务类型": cfg.get("task_type", "开发"),
        }
        rows.append([vals.get(h, "") for h in columns])

    widths = {"A": 24, "B": 46, "C": 12, "D": 10, "E": 22, "F": 20, "G": 22,
              "H": 22, "I": 12, "J": 22, "K": 20, "L": 32, "M": 90, "N": 12}
    xlsx.write_table(out_path, columns, rows, sheet_name="导出结果", widths=widths)
    return {"items": len(items), "status": status, "out": out_path}


def load_items(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("work_items", data if isinstance(data, list) else [])
