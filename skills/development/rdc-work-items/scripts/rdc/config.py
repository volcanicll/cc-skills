# -*- coding: utf-8 -*-
"""配置加载：所有环境相关变量集中于此，可通过 --config config.yaml 自定义。

纯标准库：YAML 用内置 yamlio 解析，JSON 直接 json.load。
"""
import json
import os

from . import yamlio

DEFAULTS = {
    "auth_file": "auth.json",            # 鉴权数据保存/读取位置
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
    "domain": "前端开发",                  # 领域列
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
    # ---- 工作量统计（git）----
    "git_author": "YOUR_GIT_AUTHOR",
    "git_since": "",                       # 默认空=按参数传入
    "git_until": "",
    "repos": [],                           # 待扫描的 git 仓库列表（绝对路径）
    # ---- Excel 模板列 ----
    "excel_columns": ["编号", "标题", "工作项类型", "状态", "指派给", "更新时间",
                      "计划开始时间", "实际完成时间", "初始估计", "创建人", "创建时间",
                      "团队", "详细说明", "任务类型"],
}

CONFIG_FILES = ["rdc-config.yaml", "rdc-config.yml", "rdc-config.json",
                os.path.expanduser("~/.config/rdc-work-items.yaml")]


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
