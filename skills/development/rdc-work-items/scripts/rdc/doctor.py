# -*- coding: utf-8 -*-
"""环境自检（doctor）：配置完整性 / 鉴权时效 / 调试端口 / git 仓库 / 平台信息。

纯标准库，只读检查、不修改任何状态、不自动启动浏览器。
run() 返回 (ok, lines)；ok=False 表示存在必须修复的问题（配置缺失等），
告警（⚠）不阻断。
"""
import os
import platform
import subprocess

from . import auth, config

# 与 config.FIELD_META / config.PLATFORM_FIELDS 同源，勿单独维护
REQUIRED = config.PLATFORM_FIELDS


def _check_repo(path):
    if not os.path.isdir(path):
        return False, "目录不存在"
    r = subprocess.run(["git", "-C", path, "rev-parse", "--git-dir"],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return False, (r.stderr or "不是 git 仓库").strip()
    return True, "git 仓库 OK"


def run(cfg=None, auth_path=None):
    """执行自检，返回 (ok, lines)。ok=False 表示存在阻断性问题。"""
    cfg = cfg or config.load_config()
    auth_path = auth_path or cfg.get("auth_file", "auth.json")
    lines = []
    problems = 0
    warnings = 0

    lines.append(f"平台: {platform.system()} {platform.release()} | Python {platform.python_version()}")

    # ---- 配置完整性 ----
    lines.append("[配置]")
    for key, label in REQUIRED:
        if config.is_placeholder(cfg.get(key)):
            problems += 1
            lines.append(f"  ❌ {label}（{key}）未配置，请补充后重试")
        else:
            lines.append(f"  ✅ {label}（{key}）已配置")
    if config.is_placeholder(cfg.get("git_author")):
        warnings += 1
        lines.append("  ⚠ git_author 未配置（stats 将统计全部作者的提交，如需只统计本人请补充）")
    else:
        lines.append("  ✅ git_author 已配置")

    # ---- 鉴权 ----
    lines.append("[鉴权]")
    if not os.path.exists(auth_path):
        warnings += 1
        lines.append(f"  ⚠ 未找到登录信息文件 {auth_path}，请先获取登录信息")
    else:
        try:
            a = auth.load_auth(auth_path)
        except Exception as e:
            warnings += 1
            lines.append(f"  ⚠ 鉴权文件读取失败：{e}")
            a = None
        if a:
            stale = auth.auth_is_stale(a, cfg.get("auth_max_age_hours", 12))
            src = a.get("source", "cdp")
            if stale:
                warnings += 1
                lines.append(f"  ⚠ 鉴权可能已过期（提取于 {a.get('fetched_at')}，来源 {src}），"
                             f"如遇 403 请重新获取登录信息")
            else:
                lines.append(f"  ✅ 鉴权有效（提取于 {a.get('fetched_at')}，来源 {src}）")
            for k in ("x-api-key", "x-auth-value", "x-emp-no", "x-tenant-id"):
                if not (a.get("headers") or {}).get(k):
                    warnings += 1
                    lines.append(f"  ⚠ 鉴权缺少请求头 {k}，建议重新获取登录信息")

    # ---- 浏览器调试端口 ----
    lines.append("[浏览器调试端口]")
    try:
        ws_url = auth.discover_ws_url(cfg)
        lines.append(f"  ✅ 已发现调试浏览器：{ws_url}")
    except RuntimeError as e:
        browser = auth.find_browser(cfg)
        if browser:
            warnings += 1
            lines.append(f"  ⚠ 未发现已开调试端口的浏览器（{e}）。"
                         f"已找到浏览器 {os.path.basename(browser)}，可自动获取登录信息")
        else:
            warnings += 1
            lines.append(f"  ⚠ 未发现调试浏览器，也未找到 Chrome/Edge（{e}）。"
                         f"可手动粘贴 Cookie 完成登录")

    # ---- git 仓库 ----
    lines.append("[git 仓库]")
    repos = cfg.get("repos") or []
    if not repos:
        warnings += 1
        lines.append("  ⚠ 未配置 repos（stats 无法统计提交）")
    for repo in repos:
        ok, msg = _check_repo(os.path.expanduser(repo))
        if ok:
            lines.append(f"  ✅ {repo}")
        else:
            warnings += 1
            lines.append(f"  ⚠ {repo}：{msg}")

    status = "✅ 环境检查通过" if problems == 0 and warnings == 0 else \
        ("❌ 存在必须修复的问题" if problems else "⚠ 存在可改进项")
    lines.append(f"{status}（问题 {problems}，告警 {warnings}）")
    return problems == 0, lines
