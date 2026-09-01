# 示例：工作量 Excel 离线生成

## 设计总结

- **原始输入**：`sample-work-items.json`（AI 将 `commits.json` 分组后的工作项：
  标题 / 工时 / 起止日期 / 说明）。
- **输出**：`output/8月-示例.xlsx`（14 列导出结果格式）、
  `output/导入-新建.xlsx`（清空编号、状态=新建，可直接 validate/import）。
- **零依赖**：全程仅 Python 标准库，不联网、不需要配置真实平台参数。

## 用法

```bash
python3 examples/rdc-sample/demo.py
```

## 与真实流程的衔接

1. 真实场景先用 `stats` 得到 `commits.json`，AI 分组得到 `sample-work-items.json`；
2. `build-excel` 生成工作量 Excel；
3. `prepare` 转导入文件 → `validate` → `import` 创建到研发云；
4. 从导入响应取编号，用 `update-status` 接口逐级流转状态（见 `references/workflow.md`）。
