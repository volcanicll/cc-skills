# swagger-docs

[![Node](https://img.shields.io/badge/node-%E2%89%A520-green)](https://nodejs.org)
[![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)](#%EF%B8%8F-安装)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

把任意 Swagger/OpenAPI 文档同步到本地，通过 8 种固定模式离线查询。为 AI 编程助手（Claude Code、OpenCode 等）设计，也可以直接当命令行工具用。

**核心思路**：一次性拉取 + 清洗 → 本地分仓存储 → 之后所有查询零网络、毫秒级响应、token 完全可控。

## ✨ 特性

- **零依赖** —— 仅需 Node 20+ 内置能力（原生 `fetch`），无 `npm install`、无构建
- **离线查询** —— 同步一次后全部本地读取，快且不占 AI 上下文
- **多地址分仓** —— 每个文档地址独立存储，互不干扰，支持中文别名
- **多文档合并** —— 多个 URL 可合并为一个仓（适配网关分组文档）
- **v2/v3 兼容** —— Swagger 2.0 的 body 参数 / consumes / produces 自动归一化为 OpenAPI 3 风格
- **`$ref` 自动展开** —— 详情和 schema 输出真实结构，无需追引用；带循环引用检测
- **标签修复** —— 遍历所有 operation 收集实际使用的标签（顶层 tags 声明往往不全），附接口计数
- **TS 类型直出** —— 若网关提供 `x-scripts` 预生成类型定义则直接展示
- **容错** —— 拉取失败自动重试 2 次；数据超 24 小时自动提醒更新

## 🚀 快速开始

```bash
# 1. 同步一份公开测试文档
node scripts/sync.js https://petstore3.swagger.io/api/v3/openapi.json --name petstore

# 2. 查询
node scripts/query.js tags                          # 看有哪些模块
node scripts/query.js keyword pet                   # 关键字搜接口
node scripts/query.js detail /pet/{petId} GET       # 完整详情($ref已展开)
node scripts/query.js schema Pet                    # 查数据结构定义
```

> ⚠️ 地址必须是 OpenAPI JSON 描述文件（通常是 `/v3/api-docs` 或 `/openapi.json`），不能是 `doc.html` / `swagger-ui.html` 这类 UI 页面。

## 📦 安装为 Agent 技能

### 方式一：通过 cc-skills Marketplace（推荐）

本技能收录在 [volcanicll/cc-skills](https://github.com/volcanicll/cc-skills) 的 `development-tools` 插件中：

```bash
/plugin marketplace add volcanicll/cc-skills
/plugin install development-tools@volcanic-skills
```

### 方式二：手动复制

把目录复制到技能目录即可（SKILL.md 必须在目录根部）：

```bash
cp -r swagger-docs ~/.claude/skills/swagger-docs
```

脚本通过自身路径解析数据目录，放在任何位置都能工作。之后对 AI 说"查一下订单接口"即可自动触发。

> 仓库内路径为 `skills/development/swagger-docs/`；在仓库根目录使用时把命令前缀换成
> `node skills/development/swagger-docs/scripts/...` 即可。

## 🗂️ 多地址管理

每个地址一个独立数据仓，key 由 URL 自动生成，可用 `--name` 覆盖：

```bash
$ node scripts/sync.js https://a.com/system-service/v3/api-docs --name 系统

$ node scripts/sync.js https://b.com/park-service/v3/api-docs --name 停车

# 查看所有仓
$ node scripts/query.js stores
数据仓列表:
- **系统**
  地址: https://a.com/system-service/v3/api-docs
  接口数: 307 | 同步: 2025-01-01T00:00:00.000Z | 别名: 系统
- **停车**
  ...

# 单仓时自动选择；多仓时必须用 -s 指定
$ node scripts/query.js -s 停车 tags
```

多个 URL 写在同一条命令里会**合并为一个仓**。

也支持环境变量：`SWAGGER_URLS`（逗号分隔多地址）或 `SWAGGER_URL`。

## 🔍 8 种查询模式

统一入口：`node scripts/query.js [-s <仓key>] <mode> [args...]`

| 模式         | 参数              | 说明                                                 |
| ------------ | ----------------- | ---------------------------------------------------- |
| `path`       | `<路径片段>`      | 按路径模糊匹配，不区分大小写                         |
| `keyword`    | `<关键字>`        | 在接口标题(summary)和描述(description)中搜索         |
| `tag`        | `<标签名>`        | 按模块标签精确过滤                                   |
| `permission` | `<权限编码>`      | 按 x-permission 扩展字段模糊搜索                     |
| `detail`     | `<path> <METHOD>` | 完整详情：参数、请求体、响应（$ref 已展开）、TS 类型 |
| `tags`       | 无                | 所有标签 + 接口计数（含未在顶层声明的标签）          |
| `json`       | `<关键字> [max]`  | 全文搜索，返回 JSON path 列表，默认上限 200 条       |
| `schema`     | `[名称]`          | 查看 schema 定义（$ref 已展开），支持模糊匹配        |

全局选项：

- `-s, --store <key>` 指定数据仓（多仓时必填）
- `stores` 列出所有数据仓
- `-h` 帮助

## 🧹 数据清洗做了什么

1. **版本归一化**：Swagger 2.0 的 `in: body` 参数 / `consumes` / `produces` / `response.schema` 统一转为 OpenAPI 3 的 `requestBody.content` / `responses[].content`
2. **摊平操作列表**：从嵌套 paths 提取扁平数组，保留 `x-permission`、`x-operation-path` 等网关扩展字段
3. **TS 类型提取**：从 `x-scripts` 中取预生成的 TypeScript 定义
4. **标签修复**：遍历 operation 收集实际使用的标签并与顶层声明合并，附计数
5. **查询时 `$ref` 动态展开**：深度上限 4 层，循环引用标记为 `$circularRef`

## 📁 目录结构

```
skills/development/swagger-docs/
├── SKILL.md              # Agent 技能描述（AI 读这个）
├── README.md             # 本文档
├── LICENSE
├── .gitignore            # 排除运行时数据 data/
└── scripts/
    ├── sync.js           # 拉取远端文档 → 清洗 → 分仓存储（唯一联网步骤）
    └── query.js          # 离线查询入口（8 种模式）
```

`data/` 在首次 sync 时自动生成，属于个人运行时数据，请勿提交或分发。

## ❓ FAQ

**Q: 地址填了但同步失败？**
确认是 JSON 描述文件而非 UI 页面。浏览器打开应看到一大段 JSON。若接口需要登录 token，当前暂不支持鉴权头。

**Q: 数据多久更新一次？**
不会自动刷新。重新执行 `sync.js` 即覆盖对应仓；超过 24 小时 `query.js` 会输出提示。

**Q: 和 MCP 方案比有什么区别？**
MCP 版进程常驻、协议标准化，适合固定客户端接入；本 Skill 版免部署、易分发、多了 `schema` 模式和 `$ref` 展开，且 AI 可按 SKILL.md 自主编排。二者可并存。

**Q: 支持哪些 OpenAPI 版本？**
Swagger 2.0 与 OpenAPI 3.x 均可，同步时自动归一化。
