#!/usr/bin/env node
// DeepSeekHashV1 PoW 求解器 —— 直接运行官方 sha3_wasm_bg.wasm（Node 内置 WebAssembly，零 npm 依赖）
// 用法: node pow_solve.mjs <wasm路径> <challenge-hex> <prefix> <difficulty>
// 输出: {"status":0|1,"answer":<int|null>}
import { readFileSync } from "node:fs";

const [wasmPath, challenge, prefix, difficulty] = process.argv.slice(2);
const bytes = readFileSync(wasmPath);
const { instance } = await WebAssembly.instantiate(bytes, {});
const e = instance.exports;
const mem = e.memory;
const malloc = e.__wbindgen_export_0;
const stackPtr = e.__wbindgen_add_to_stack_pointer;
const enc = new TextEncoder();

const writeStr = (s) => {
  const b = enc.encode(s);
  const p = malloc(b.length, 1);
  new Uint8Array(mem.buffer, p, b.length).set(b);
  return [p, b.length];
};

const ret = stackPtr(-16);
const [cp, cl] = writeStr(challenge);
const [pp, pl] = writeStr(prefix);
e.wasm_solve(ret, cp, cl, pp, pl, Number(difficulty));
const dv = new DataView(mem.buffer);
const status = dv.getInt32(ret, true);
const answer = status === 0 ? null : Math.round(dv.getFloat64(ret + 8, true));
stackPtr(16);

process.stdout.write(JSON.stringify({ status, answer }));
