# -*- coding: utf-8 -*-
"""配置加载：所有环境相关变量集中于此，可通过 --config rdc-config.yaml 或全局配置自定义。

纯标准库：YAML 用内置 yamlio 解析/序列化，JSON 直接 json.load。
支持多平台全局配置目录（macOS/Linux 用 ~/.config，Windows 用 %APPDATA%）。
"""
import json
import os

from . import schema, yamlio

APP_NAME = "rdc-work-items"


def user_config_dir(app=APP_NAME):
    """用户配置目录（多平台）：
    - Windows: %APPDATA%\\rdc-work-items
    - macOS/Linux: ~/.config/rdc-work-items
    """
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser(r"~\AppData\Roaming")
        return os.path.join(base, app)
    return os.path.join(os.path.expanduser("~"), ".config", app)


def global_config_path():
    """全局配置文件（多平台）：
    - Windows: %APPDATA%\\rdc-work-items.yaml
    - macOS/Linux: ~/.config/rdc-work-items.yaml
    """
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser(r"~\AppData\Roaming")
        return os.path.join(base, APP_NAME + ".yaml")
    return os.path.expanduser("~/.config/rdc-work-items.yaml")


DEFAULTS = {
    "auth_file": os.path.join(user_config_dir(), "auth.json"),  # 鉴权数据（用户配置目录，勿入库）
    # ---- 研发云平台 ----
    "base_url": "https://www.srdcloud.cn/zte-rdcloud-rdc-wimbackend",
    "workspace": "YOUR_WORKSPACE",          # 工作区（接口路径/团队关联）
    "project_id": "YOUR_PROJECT_ID",                  # x-project-id 头（页面 localStorage EO_SPACE_KEY）
    "team_id": "YOUR_TEAM_ID",                # 团队（导入/导出参数）
    "tenant_id": "YOUR_TENANT_ID",                  # x-tenant-id 头
    "api_key": "YOUR_API_KEY",  # x-api-key（check-excel 需要）
    # ---- 指派人 / 归属 ----
    "assignee_emp_no": "YOUR_EMP_NO",   # x-emp-no 头 + 指派给
    "assignee_name": "YOUR_NAME",
    "team_name": "YOUR_TEAM_NAME",
    "work_item_type": "任务",
    "task_type": "开发",
    # ---- 状态流转（按顺序执行，不可跳级）----
    "status_flow": ["新建", "处理中", "已完成", "已关闭"],
    "initial_status": "新建",
    # ---- 状态流转接口（updateWorkItems/edit，不再走 Excel 导入）----
    "wic_base_url": "https://www.srdcloud.cn/zte-plm-wic-api",
    "wic_version": "V1.24.22",           # x-wic-version 头（页面版本）
    "work_item_type_key": "Task",        # workItems[].workItemTypeKey
    "state_field_id": "63f96af738aa624d3b708445",  # System_State 字段元数据 id
    # ---- CDP / Chrome ----
    "chrome_debug_port": 9222,
    "chrome_profile_dir": "~/Library/Application Support/Google/Chrome",
    "browser": "auto",                 # 自动启动时选择浏览器: auto/chrome/edge
    "chrome_path": "",                 # 浏览器可执行文件绝对路径（自动探测失败时指定）
    "auth_wait_seconds": 120,          # auth 自动启动后等待登录的最长秒数（0=不等待）
    "auth_max_age_hours": 12,          # 鉴权文件超过该时长视为过期（API 命令前提示）
    # ---- 工作量统计（git）----
    "git_author": "YOUR_GIT_AUTHOR",
    "git_since": "",                       # 默认空=按参数传入
    "git_until": "",
    "repos": [],                           # 待扫描的 git 仓库列表（绝对路径）
    # ---- Excel 模板列（单一事实源见 rdc/schema.py；仅支持在标准列内增删/排序）----
    "excel_columns": list(schema.EXPORT_COLUMNS),
}

CONFIG_FILES = ["rdc-config.yaml", "rdc-config.yml", "rdc-config.json",
                global_config_path()]


def load_config(path=None):
    cfg = dict(DEFAULTS)
    candidates = [path] if path else CONFIG_FILES
    for c in candidates:
        if c and os.path.exists(c):
            with open(c, encoding="utf-8") as f:
                if c.endswith(".json"):
                    data = json.load(f) or {}
                else:
                    data = yamlio.safe_load(f.read()) or {}
            if not isinstance(data, dict):
                raise ValueError(f"配置文件 {c} 顶层必须是 mapping")
            cfg.update(data)
            break
    # 路径展开
    for k in ("chrome_profile_dir",):
        if isinstance(cfg.get(k), str):
            cfg[k] = os.path.expanduser(cfg[k])
    return cfg


def write_private_file(path, text):
    """写入文件并收紧权限：目录 0700、文件 0600（POSIX 生效；Windows 下 mode 参数被忽略）。

    用于 auth.json / 全局配置等含会话凭据与 API Key 的文件，
    避免同机其它账号可读（默认 umask 022 下 open() 会产生 0644）。
    """
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, mode=0o700, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    try:
        os.chmod(path, 0o600)  # 兜底：覆盖 umask / 既有文件权限
    except OSError:
        pass  # 非 POSIX 平台无 chmod 语义，忽略
    return path


def write_global_config(data, path=None):
    """把配置写入全局配置文件（多平台路径，0600），返回写入路径。"""
    path = path or global_config_path()
    return write_private_file(path, yamlio.dump(data))
