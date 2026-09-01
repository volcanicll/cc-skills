# -*- coding: utf-8 -*-
"""yamlio（内置 YAML 子集解析器）测试：python3 tests/test_yamlio.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "rdc"))

import yamlio


def test_basic_map():
    d = yamlio.load("a: 1\nb: hello\nc: true\nd: null\n")
    assert d == {"a": 1, "b": "hello", "c": True, "d": None}, d


def test_nested_and_list():
    text = """
base: "https://x"
status_flow:
  - 新建
  - 处理中
  - 已完成
repos:
  - /a
  - /b
initial_status: "新建"
"""
    d = yamlio.load(text)
    assert d["base"] == "https://x"
    assert d["status_flow"] == ["新建", "处理中", "已完成"]
    assert d["repos"] == ["/a", "/b"]
    assert d["initial_status"] == "新建"


def test_comments_and_quoted_hash():
    text = """
# 顶层注释
url: "https://a.com/#frag"   # 行尾注释
plain: value # comment
q: 'single # not comment'
"""
    d = yamlio.load(text)
    assert d["url"] == "https://a.com/#frag"
    assert d["plain"] == "value"
    assert d["q"] == "single # not comment"


def test_empty():
    assert yamlio.load("") == {}
    assert yamlio.load("# only comment\n") == {}


def test_quoted_key():
    d = yamlio.load('"k1": v\n')
    assert d == {"k1": "v"}


def test_config_example():
    here = os.path.dirname(__file__)
    cfg_path = os.path.join(here, "..", "config.example.yaml")
    d = yamlio.load(open(cfg_path, encoding="utf-8").read())
    assert d["workspace"] == "YOUR_WORKSPACE"
    assert d["status_flow"][0] == "新建"
    assert d["chrome_debug_port"] == 9222


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("yamlio tests passed")
