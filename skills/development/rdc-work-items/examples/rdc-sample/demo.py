# -*- coding: utf-8 -*-
"""离线示例：用样例 sample-work-items.json 走 build-excel → prepare → summary（不联网、零依赖）。

运行：python3 examples/rdc-sample/demo.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "..", "scripts")
sys.path.insert(0, SCRIPTS)

from rdc import config, excelgen, prepare  # noqa: E402


def main():
    cfg = config.load_config()
    items = excelgen.load_items(os.path.join(HERE, "sample-work-items.json"))

    out_dir = os.path.join(HERE, "output")
    os.makedirs(out_dir, exist_ok=True)

    src = os.path.join(out_dir, "8月-示例.xlsx")
    excelgen.build(cfg, items, src, status="新建")
    print(f"[1] 已生成工作量 Excel：{src}（{len(items)} 条）")

    imp = os.path.join(out_dir, "导入-新建.xlsx")
    prepare.prepare(src, imp, status="新建")
    print(f"[2] 已生成导入文件：{imp}")

    print("[3] 内容摘要：")
    for it in prepare.summarize(src):
        print(f"    {it['编号'] or '(新)'} | {it['状态']} | {it['标题']}")

    print("✅ 示例完成（离线，未调用任何平台接口）")


if __name__ == "__main__":
    main()
