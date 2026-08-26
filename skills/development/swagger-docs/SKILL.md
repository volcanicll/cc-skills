---
name: swagger-docs
description: 查询 Swagger/OpenAPI 接口文档（本地离线缓存）。支持按路径/关键字/标签/权限编码搜索接口、查看接口详情与 TypeScript 类型定义、查询 schema。当用户提到"查接口"、"API 文档"、"swagger"、"openapi"、"接口详情"、"权限编码"、"schema"等时使用。
---

# Swagger 接口文档离线查询

本地缓存清洗后的接口文档，通过固定脚本查询，**不要**直接 curl 远端地址。

**Skill 根目录**：即本 SKILL.md 所在目录。下文 `<SKILL>` 均指该目录的绝对路径。

## 数据仓

每个 OpenAPI 地址对应一个独立数据仓 `data/<storeKey>/`，互不干扰。
`<storeKey>` 由 URL 自动生成，也可在同步时用 `--name` 指定别名。

查看已有数据仓：

```bash
node <SKILL>/scripts/query.js stores
```

## 使用步骤

### 1. 确定数据是否可用

```bash
node <SKILL>/scripts/query.js stores
```

- **没有目标地址的仓** → 先同步（见下）
- **有仓但 syncedAt 超过 24 小时**，或用户提到"新接口/最新文档" → 重新同步
- **有且新鲜** → 直接查询

### 2. 同步（唯一联网步骤）

```bash
# 单地址
node <SKILL>/scripts/sync.js https://example.com/service/v3/api-docs

# 多地址合并为一个仓（适合网关分组文档）
node <SKILL>/scripts/sync.js https://a.com/v3/api-docs https://b.com/v3/api-docs

# 用易记别名建仓（推荐）
node <SKILL>/scripts/sync.js https://example.com/v3/api-docs --name 项目简称
```

失败自动重试 2 次；脚本只依赖 Node 20+ 内置能力，无需安装任何包。
地址必须为 OpenAPI JSON 描述文件（通常是 `/v3/api-docs`），不能是 `doc.html` 等 UI 页面。
也可通过环境变量提供地址：`SWAGGER_URLS`（逗号分隔多地址）或 `SWAGGER_URL`（单地址）。

### 3. 查询（8 种模式）

```bash
node <SKILL>/scripts/query.js [-s <storeKey>] <mode> [args...]
```

只有一个仓时 `-s` 可省略；多个仓时必须指定（脚本会列出可选值）。

| 场景 | 命令 |
|---|---|
| 大概知道路径片段 | `query.js path users` |
| 只知道功能名 | `query.js keyword 创建订单` |
| 知道模块标签 | `query.js tag 订单管理` |
| 有权限编码 | `query.js permission ABCD1234` |
| 要完整参数/响应定义 | `query.js detail /users/{id} GET` |
| 浏览所有功能模块 | `query.js tags` |
| 全文搜索任意字段 | `query.js json 手机号 50` |
| 查某个数据结构定义 | `query.js schema UserDto` |

### 4. 典型工作流

1. **找接口**：`tags` 看模块 → `tag` 或 `keyword` 定位 → `detail` 取完整定义
2. `detail` 输出中 `$ref` 已自动展开为真实结构；TypeScript 类型直接可用
3. `schema` 名不确定时给模糊名即可：单个匹配直接展开，多个返回候选列表
4. 所有查询纯读本地文件、无网络、可并行调用；结果多于 1 个时返回列表，需再 `detail` 细看单个接口

## 注意事项

- 若远端需要登录 token 而当前无法访问，sync 会失败并明确报错
- `data/` 目录为个人运行时数据，分发/提交版本库时应排除
