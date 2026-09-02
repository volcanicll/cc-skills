# -*- coding: utf-8 -*-
"""极简 YAML 子集解析器（纯标准库，替代 pyyaml）。

支持本项目配置文件所需的子集：
- 缩进嵌套的 mapping（`key: value`）
- 块状 sequence（`- item`）
- 单/双引号字符串、数字、布尔、null
- 行注释与行尾注释（引号内的 # 不视为注释）

不支持：锚点/别名、多行字符串（| >）、流式 {}/[]、复杂嵌套（如 `- key: v`）。
复杂配置可改用 JSON（rdc-config.json，同样被支持）。
"""
import re

_NUM = re.compile(r"[-+]?(\d+\.?\d*|\.\d+)$")
_INT = re.compile(r"[-+]?\d+$")


def _strip_comment(line):
    """去掉行尾注释（引号内 # 不处理）。"""
    in_s = in_d = False
    for i, ch in enumerate(line):
        if ch == '"' and not in_s:
            in_d = not in_d
        elif ch == "'" and not in_d:
            in_s = not in_s
        elif ch == "#" and not in_s and not in_d:
            if i == 0 or line[i - 1] in " \t":
                return line[:i].rstrip()
    return line.rstrip()


def _parse_value(text):
    text = text.strip()
    if not text:
        return None
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        return text[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if len(text) >= 2 and text[0] == "'" and text[-1] == "'":
        return text[1:-1]
    if text in ("null", "Null", "NULL", "~"):
        return None
    if text == "[]":
        return []
    if text == "{}":
        return {}
    if text in ("true", "True", "TRUE"):
        return True
    if text in ("false", "False", "FALSE"):
        return False
    if _INT.fullmatch(text):
        try:
            return int(text)
        except ValueError:
            pass
    if _NUM.fullmatch(text):
        try:
            return float(text)
        except ValueError:
            pass
    if text.startswith("[") or text.startswith("{"):
        raise ValueError(
            f"不支持的 YAML flow 语法: {text[:40]!r}。本项目配置子集仅支持块状 list/map，"
            "复杂配置请改用 rdc-config.json")
    return text


def _tokenize(text):
    toks = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        s = raw.expandtabs(4)
        indent = len(s) - len(s.lstrip())
        content = _strip_comment(s.strip())
        if content:
            toks.append((indent, content))
    return toks


def load(text):
    """解析 YAML 文本，返回 dict/list。空输入返回 {}。"""
    toks = _tokenize(text)
    if not toks:
        return {}

    def parse_seq(idx, indent):
        items = []
        while idx < len(toks) and toks[idx][0] == indent \
                and toks[idx][1].startswith("- "):
            rest = toks[idx][1][2:].strip()
            idx += 1
            if rest:
                items.append(_parse_value(rest))
            elif idx < len(toks) and toks[idx][0] > indent:
                v, idx = parse_block(idx, toks[idx][0])
                items.append(v)
            else:
                items.append(None)
        return items, idx

    def parse_map(idx, indent):
        d = {}
        while idx < len(toks) and toks[idx][0] == indent \
                and not toks[idx][1].startswith("- "):
            content = toks[idx][1]
            idx += 1
            if ":" not in content:
                continue  # 跳过无法解析的行
            key, _, rest = content.partition(":")
            key = _parse_value(key.strip())
            rest = rest.strip()
            if rest:
                d[key] = _parse_value(rest)
            elif idx < len(toks) and toks[idx][0] > indent:
                v, idx = parse_block(idx, toks[idx][0])
                d[key] = v
            else:
                d[key] = None
        return d, idx

    def parse_block(idx, indent):
        if toks[idx][1].startswith("- "):
            return parse_seq(idx, indent)
        return parse_map(idx, indent)

    v, _ = parse_block(0, toks[0][0])
    return v or {}


def safe_load(text):
    """兼容 yaml.safe_load 接口。"""
    return load(text)


# ---------------------------------------------------------------------------
# 序列化（写入全局配置用，支持本项目配置子集）
# ---------------------------------------------------------------------------

_SCALAR_LIKE = re.compile(r"^(null|~|true|false|[-+]?\d+\.?\d*|[-+]?\d+)$", re.I)


def _dump_scalar(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    if (s == "" or s != s.strip() or _SCALAR_LIKE.fullmatch(s.strip())
            or any(ch in s for ch in "#:{}[],&*!|>'\"%@`")):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def dump(data, indent=2):
    """把 dict 序列化为 YAML（与 load 支持的子集对称）。"""
    pad = " " * indent
    lines = []

    def emit(d, level):
        for k, v in d.items():
            key = _dump_scalar(k)
            prefix = pad * level
            if isinstance(v, dict):
                lines.append(f"{prefix}{key}:")
                emit(v, level + 1)
            elif isinstance(v, list):
                if not v:
                    lines.append(f"{prefix}{key}: []")
                    continue
                lines.append(f"{prefix}{key}:")
                for item in v:
                    if isinstance(item, dict):
                        lines.append(f"{prefix}{pad}-")
                        emit(item, level + 2)
                    else:
                        lines.append(f"{prefix}{pad}- {_dump_scalar(item)}")
            else:
                lines.append(f"{prefix}{key}: {_dump_scalar(v)}")

    emit(data, 0)
    return "\n".join(lines) + ("\n" if lines else "")
