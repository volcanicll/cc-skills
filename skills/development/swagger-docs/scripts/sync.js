#!/usr/bin/env node
// 拉取 Swagger 文档，清洗归一化后按地址分仓写入 data/<store>/
// 用法: node scripts/sync.js <url1> [url2...] [--name 别名]
//       无参数时回退 SWAGGER_URLS / SWAGGER_URL 环境变量，最后回退内置默认地址
import { mkdirSync, writeFileSync, existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const SKILL_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const DATA_ROOT = join(SKILL_ROOT, "data");

function parseArgs(argv) {
  const urls = [];
  let name;
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--name") name = argv[++i];
    else urls.push(argv[i]);
  }
  return { urls, name };
}

export function storeKeyFor(url) {
  const u = new URL(url);
  const raw = `${u.hostname}${u.pathname.replace(/\/$/, "")}`;
  return (raw.replace(/[^a-zA-Z0-9]+/g, "_").replace(/^_+|_+$/g, "") || "default").slice(0, 80);
}

async function fetchDoc(url, retries = 2) {
  for (let attempt = 0; ; attempt++) {
    try {
      const res = await fetch(url, {
        signal: AbortSignal.timeout(15000),
        headers: { Accept: "application/json" },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      if (attempt >= retries) throw e;
      console.error(`[sync] 拉取失败(第${attempt + 1}次),重试: ${e.message}`);
      await new Promise((r) => setTimeout(r, 1000));
    }
  }
}

const DEFAULT_MEDIA_TYPE = "application/json";

function normalizeOperation(doc, operation) {
  const consumes = operation.consumes ?? doc.consumes;
  const produces = operation.produces ?? doc.produces;
  const consumeTypes = consumes?.length ? consumes : [DEFAULT_MEDIA_TYPE];
  const produceTypes = produces?.length ? produces : [DEFAULT_MEDIA_TYPE];

  let requestBody;
  if (operation.requestBody) {
    requestBody = operation.requestBody;
  } else {
    const bodyParam = operation.parameters?.find((p) => p.in === "body");
    if (bodyParam) {
      const content = {};
      for (const mt of consumeTypes)
        content[mt] = { schema: bodyParam.schema ?? { type: bodyParam.type, format: bodyParam.format } };
      requestBody = { description: bodyParam.description, required: bodyParam.required, content };
    }
  }

  let responses;
  if (operation.responses) {
    responses = {};
    for (const [status, res] of Object.entries(operation.responses)) {
      if (!res) continue;
      if (res.content || !res.schema) {
        responses[status] = res;
        continue;
      }
      const content = {};
      for (const mt of produceTypes) content[mt] = { schema: res.schema };
      responses[status] = { ...res, content };
    }
  }

  const tsScript = operation["x-scripts"]?.find(
    (s) => s.scriptType === "TYPESCRIPT" && s.scriptName === "TypeScript"
  );

  return {
    parameters: operation.parameters?.filter((p) => p.in !== "body"),
    requestBody,
    responses,
    permissionCode: operation["x-permission"],
    operationPath: operation["x-operation-path"],
    operationMethod: operation["x-operation-method"],
    typeScriptTypes: tsScript?.content,
  };
}

function loadIndex() {
  const file = join(DATA_ROOT, "index.json");
  return existsSync(file) ? JSON.parse(readFileSync(file, "utf8")) : { stores: {} };
}

function saveIndex(index) {
  mkdirSync(DATA_ROOT, { recursive: true });
  writeFileSync(join(DATA_ROOT, "index.json"), JSON.stringify(index, null, 2));
}

async function main() {
  let { urls, name } = parseArgs(process.argv.slice(2));
  if (urls.length === 0) {
    // 回退链：SWAGGER_URLS > SWAGGER_URL；都没有则报错
    if (process.env.SWAGGER_URLS) urls = process.env.SWAGGER_URLS.split(",").map((u) => u.trim()).filter(Boolean);
    else if (process.env.SWAGGER_URL) urls = [process.env.SWAGGER_URL];
  }
  if (urls.length === 0) {
    console.error(
      "用法: node scripts/sync.js <openapi-json-url...> [--name 别名]\n" +
      "示例: node scripts/sync.js https://petstore3.swagger.io/api/v3/openapi.json --name petstore\n" +
      "也可通过环境变量 SWAGGER_URLS / SWAGGER_URL 提供\n" +
      "注意: 地址需为 OpenAPI JSON 描述文件(通常是 /v3/api-docs)，不是 doc.html 等 UI 页面"
    );
    process.exit(1);
  }
  for (const url of urls) new URL(url); // 校验格式

  console.error(`[sync] 目标: ${urls.join(", ")}`);
  const docs = [];
  for (const url of urls) {
    console.error(`[sync] 拉取 ${url} ...`);
    docs.push(await fetchDoc(url));
  }

  // 多文档合并：paths/tags/schemas 后者覆盖前者
  const doc = Object.assign({}, ...docs);
  doc.paths = Object.assign({}, ...docs.map((d) => d.paths || {}));
  doc.components = { schemas: Object.assign({}, ...docs.map((d) => d.components?.schemas)) };
  doc.definitions = Object.assign({}, ...docs.map((d) => d.definitions));

  // 清洗：摊平为操作列表
  const apis = [];
  for (const [path, pathItem] of Object.entries(doc.paths || {})) {
    for (const [method, op] of Object.entries(pathItem)) {
      if (!op || typeof op !== "object" || !("summary" in op)) continue;
      apis.push({
        path,
        method: method.toUpperCase(),
        summary: op.summary,
        description: op.description,
        tags: op.tags || [],
        operationId: op.operationId,
        deprecated: op.deprecated || false,
        ...normalizeOperation(doc, op),
      });
    }
  }
  const schemas = { ...(doc.components?.schemas || {}), ...(doc.definitions || {}) };

  const declaredTags = new Map((doc.tags || []).map((t) => [t.name, t.description]));
  const tagCounts = {};
  for (const api of apis) for (const t of api.tags) tagCounts[t] = (tagCounts[t] || 0) + 1;

  // 分仓存储：优先用 --name 别名，否则由 URL 自动生成 key
  const storeKey = name || storeKeyFor(urls[0]);
  const storeDir = join(DATA_ROOT, storeKey);
  mkdirSync(storeDir, { recursive: true });
  writeFileSync(join(storeDir, "apis.json"), JSON.stringify(apis));
  writeFileSync(join(storeDir, "schemas.json"), JSON.stringify(schemas));

  const meta = {
    storeKey,
    name: name || null,
    urls,
    syncedAt: new Date().toISOString(),
    apiCount: apis.length,
    schemaCount: Object.keys(schemas).length,
    tags: [...new Set(apis.flatMap((a) => a.tags))].sort().map((tag) => ({
      name: tag,
      description: declaredTags.get(tag),
      count: tagCounts[tag],
    })),
  };
  writeFileSync(join(storeDir, "meta.json"), JSON.stringify(meta, null, 2));

  const index = loadIndex();
  index.stores[storeKey] = { name: meta.name, urls, syncedAt: meta.syncedAt, apiCount: meta.apiCount };
  saveIndex(index);

  console.error(`[sync] 完成 → data/${storeKey}/: ${apis.length} 个接口, ${Object.keys(schemas).length} 个 schema`);
  console.error(`[sync] 查询时使用: query.js -s ${storeKey} <mode> ...`);
}

main().catch((e) => {
  console.error(`[sync] 失败: ${e.message}`);
  process.exit(1);
});
