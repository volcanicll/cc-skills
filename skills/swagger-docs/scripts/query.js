#!/usr/bin/env node
// 离线查询本地清洗后的 Swagger 数据（由 sync.js 按地址分仓存于 data/<store>/）
// 用法: node scripts/query.js [-s <storeKey>] <mode> [args...]
//       仅有一个仓时 -s 可省略
import { readFileSync, existsSync, statSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const SKILL_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const DATA_ROOT = join(SKILL_ROOT, "data");

function parseArgs(argv) {
  const positional = [];
  let store;
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "-s" || argv[i] === "--store") store = argv[++i];
    else positional.push(argv[i]);
  }
  return { store, positional };
}

function listStores() {
  if (!existsSync(DATA_ROOT)) return [];
  return readdirSync(DATA_ROOT).filter((d) => existsSync(join(DATA_ROOT, d, "meta.json")));
}

function resolveStore(requested) {
  const available = listStores();
  if (available.length === 0) {
    console.error(`本地无数据。请先运行: node scripts/sync.js <swagger文档地址>`);
    process.exit(1);
  }
  if (requested) {
    if (!available.includes(requested)) {
      console.error(`仓 "${requested}" 不存在。可用: ${available.join(", ")}`);
      process.exit(1);
    }
    return requested;
  }
  // 未指定且只有一个仓 → 自动选择；多个 → 报错列出
  if (available.length === 1) return available[0];
  console.error(`存在多个数据仓，请用 -s 指定:\n${available.map((s) => `  - ${s}`).join("\n")}`);
  process.exit(1);
}

let STORE;
function dataFile(name) {
  return join(DATA_ROOT, STORE, name);
}
function load(name) {
  const file = dataFile(name);
  if (!existsSync(file)) {
    console.error(`数据文件不存在: ${file}\n请先运行: node scripts/sync.js`);
    process.exit(1);
  }
  return JSON.parse(readFileSync(file, "utf8"));
}

function checkStale() {
  try {
    const age = Date.now() - statSync(dataFile("meta.json")).mtimeMs;
    if (age > 24 * 3600 * 1000) {
      console.error(`[提示] 数据已 ${Math.floor(age / 86400000)} 天未更新，建议: node scripts/sync.js`);
    }
  } catch {}
}

const schemasCache = {};
const schemas = () => (schemasCache.v ||= load("schemas.json"));
const apis = () => load("apis.json");

// $ref 解析：{"$ref":"#/components/schemas/X"} → schema 内容，带环检测与深度限制
function resolveRefs(node, depth = 0, seen = new Set()) {
  if (depth > 4 || !node || typeof node !== "object") return node;
  if (Array.isArray(node)) return node.map((n) => resolveRefs(n, depth, seen));
  const ref = node["$ref"];
  if (typeof ref === "string" && ref.startsWith("#/")) {
    const name = ref.split("/").pop();
    const target = schemas()[name];
    if (!target) return { ...node, description: `[未找到引用: ${ref}]` };
    if (seen.has(name)) return { $circularRef: ref };
    return resolveRefs(target, depth + 1, new Set([...seen, name]));
  }
  const out = {};
  for (const [k, v] of Object.entries(node)) out[k] = resolveRefs(v, depth, seen);
  return out;
}

function fmtSchema(schema) {
  return JSON.stringify(resolveRefs(schema), null, 2);
}

function apiToMarkdown(api) {
  const lines = [`# ${api.method} ${api.path}`, ""];
  if (api.summary) lines.push(`**摘要**: ${api.summary}`, "");
  if (api.description) lines.push(`**描述**: ${api.description}`, "");
  if (api.tags?.length) lines.push(`**标签**: ${api.tags.join(", ")}`, "");
  if (api.permissionCode) lines.push(`**权限编码**: ${api.permissionCode}`, "");
  if (api.deprecated) lines.push("> ⚠️ **已废弃**", "");
  if (api.operationId) lines.push(`**操作ID**: ${api.operationId}`, "");

  if (api.parameters?.length) {
    lines.push("## 参数", "");
    for (const p of api.parameters) {
      lines.push(`- **${p.name}** (${p.in}) - ${p.required ? "**必需**" : "可选"}`);
      if (p.description) lines.push(`  - 描述: ${p.description}`);
      if (p.schema) lines.push(`  - 类型: \`${JSON.stringify(resolveRefs(p.schema))}\``);
    }
    lines.push("");
  }

  if (api.requestBody) {
    lines.push("## 请求体", "");
    if (api.requestBody.description) lines.push(api.requestBody.description, "");
    for (const [mt, c] of Object.entries(api.requestBody.content || {})) {
      lines.push(`**Content-Type**: ${mt}`, "```json", fmtSchema(c.schema), "```");
    }
    lines.push("");
  }

  if (api.responses) {
    lines.push("## 响应", "");
    for (const [status, res] of Object.entries(api.responses)) {
      lines.push(`### ${status}`);
      if (res.description) lines.push(res.description);
      for (const [mt, c] of Object.entries(res.content || {})) {
        lines.push(`**Content-Type**: ${mt}`, "```json", fmtSchema(c.schema), "```");
      }
      lines.push("");
    }
  }

  if (api.typeScriptTypes) {
    lines.push("## TypeScript 类型定义", "", "```typescript", api.typeScriptTypes, "```", "");
  }
  return lines.join("\n");
}

function apiListLine(api) {
  let s = `- **${api.method} ${api.path}**`;
  if (api.summary) s += `\n  ${api.summary}`;
  if (api.tags?.length) s += `\n  标签: ${api.tags.join(", ")}`;
  return s;
}

const MODES = {
  path(kw) {
    const k = kw.toLowerCase();
    const r = apis().filter((a) => a.path.toLowerCase().includes(k));
    if (r.length === 0) return `未找到包含 "${kw}" 的API路径`;
    if (r.length === 1) return apiToMarkdown(r[0]);
    return [`找到 ${r.length} 个API:\n`, ...r.map(apiListLine)].join("\n");
  },
  keyword(kw) {
    const k = kw.toLowerCase();
    const r = apis().filter(
      (a) => (a.summary || "").toLowerCase().includes(k) || (a.description || "").toLowerCase().includes(k)
    );
    if (r.length === 0) return `未找到包含 "${kw}" 的API`;
    if (r.length === 1) return apiToMarkdown(r[0]);
    return [`找到 ${r.length} 个API:\n`, ...r.map(apiListLine)].join("\n");
  },
  tag(name) {
    const r = apis().filter((a) => a.tags.includes(name));
    if (r.length === 0) return `未找到标签为 "${name}" 的API`;
    return [`找到 ${r.length} 个API:\n`, ...r.map(apiListLine)].join("\n");
  },
  permission(code) {
    const k = code.toLowerCase();
    const r = apis().filter((a) => (a.permissionCode || "").toLowerCase().includes(k));
    if (r.length === 0) return `未找到权限编码包含 "${code}" 的API`;
    if (r.length === 1) return apiToMarkdown(r[0]);
    return [`找到 ${r.length} 个API:\n`, ...r.map(apiListLine)].join("\n");
  },
  detail(path, method) {
    if (!method) return "用法: query.js detail <path> <METHOD>";
    const api = apis().find((a) => a.path === path && a.method === method.toUpperCase());
    return api ? apiToMarkdown(api) : `未找到 ${method.toUpperCase()} ${path} 的API`;
  },
  tags() {
    const meta = load("meta.json");
    if (!meta.tags?.length) return "未找到任何标签";
    const sorted = [...meta.tags].sort((a, b) => b.count - a.count);
    return [
      `共 ${sorted.length} 个标签 (来源: ${meta.urls.join(", ")}, 同步于 ${meta.syncedAt}):\n`,
      ...sorted.map((t) => {
        let s = `- **${t.name}** (${t.count} 个接口)`;
        if (t.description) s += `\n  ${t.description}`;
        return s;
      }),
    ].join("\n");
  },
  json(kw, maxResults) {
    const doc = {
      paths: Object.fromEntries(apis().map((a) => [`${a.path}#${a.method}`, a])),
      components: { schemas: schemas() },
    };
    const max = Number(maxResults) > 0 ? Number(maxResults) : 200;
    const k = kw.toLowerCase();
    const results = [];
    let truncated = false;
    const walk = (node, path) => {
      if (truncated) return;
      if (typeof node === "string") {
        if (node.toLowerCase().includes(k)) results.push(path || "<root>");
        else if (results.length >= max) truncated = true;
        return;
      }
      if (results.length >= max) { truncated = true; return; }
      if (Array.isArray(node)) { node.forEach((item, i) => walk(item, `${path}[${i}]`)); return; }
      if (node && typeof node === "object") {
        for (const [key, value] of Object.entries(node)) {
          const keyPath = path ? `${path}.${key}` : key;
          if (key.toLowerCase().includes(k)) results.push(keyPath);
          walk(value, keyPath);
          if (truncated) break;
        }
      }
    };
    walk(doc, "");
    if (results.length === 0) return `未找到包含 "${kw}" 的内容`;
    return [`找到 ${results.length} 处匹配${truncated ? "（已截断）" : ""}:\n`, ...results.map((p) => `- ${p}`)].join("\n");
  },
  schema(name) {
    const all = schemas();
    if (!name) return [`共 ${Object.keys(all).length} 个 schema:\n`, ...Object.keys(all).map((s) => `- ${s}`)].join("\n");
    if (all[name]) return `# Schema: ${name}\n\n\`\`\`json\n${JSON.stringify(resolveRefs(all[name]), null, 2)}\n\`\`\``;
    const k = name.toLowerCase();
    const matches = Object.keys(all).filter((s) => s.toLowerCase().includes(k));
    if (matches.length === 1) return `# Schema: ${matches[0]}\n\n\`\`\`json\n${JSON.stringify(resolveRefs(all[matches[0]]), null, 2)}\n\`\`\``;
    if (matches.length === 0) return `未找到 schema "${name}"`;
    return [`匹配到 ${matches.length} 个 schema:\n`, ...matches.map((s) => `- ${s}`)].join("\n");
  },
};

const HELP = `用法: node scripts/query.js [-s <store>] <mode> [args...]

模式:
  path <关键字>              按路径模糊搜索接口
  keyword <关键字>           按 summary/description 搜索
  tag <标签名>               按标签精确搜索
  permission <权限编码>       按权限编码模糊搜索
  detail <path> <METHOD>     接口完整详情($ref已展开)
  tags                       列出所有标签及计数
  json <关键字> [max]        全局JSON路径搜索
  schema [名称]              查看/搜索schema定义($ref已展开)

选项:
  -s, --store <key>          指定数据仓(多地址时必填，单仓自动选择)
  stores                     列出所有数据仓`;

checkStale();
const raw = process.argv.slice(2);
if (raw.length === 0 || raw[0] === "-h" || raw[0] === "--help") {
  console.log(HELP);
  process.exit(0);
}
const { store: requested, positional } = parseArgs(raw);

if (positional[0] === "stores") {
  const index = existsSync(join(DATA_ROOT, "index.json"))
    ? JSON.parse(readFileSync(join(DATA_ROOT, "index.json"), "utf8"))
    : { stores: {} };
  const entries = Object.entries(index.stores);
  if (entries.length === 0) {
    console.log("暂无数据仓。运行: node scripts/sync.js <swagger文档地址>");
  } else {
    console.log(
      ["数据仓列表:\n", ...entries.map(([k, v]) => `- **${k}**\n  地址: ${v.urls.join(", ")}\n  接口数: ${v.apiCount} | 同步: ${v.syncedAt}${v.name ? ` | 别名: ${v.name}` : ""}`)].join("\n")
    );
  }
  process.exit(0);
}

STORE = resolveStore(requested);
const [mode, ...args] = positional;
if (!MODES[mode]) {
  console.error(`未知模式: ${mode}\n\n${HELP}`);
  process.exit(1);
}
console.log(MODES[mode](...args));
