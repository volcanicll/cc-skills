#!/usr/bin/env node
/**
 * Basic unit tests for swagger-docs utility functions.
 */

import assert from "node:assert";
import { storeKeyFor } from "../scripts/sync.js";

// 1. Test storeKey generation
const url1 = "https://petstore3.swagger.io/api/v3/openapi.json";
const key1 = storeKeyFor(url1);
assert.strictEqual(key1, "petstore3_swagger_io_api_v3_openapi_json");

const url2 = "https://api.example.com/v3/api-docs/";
const key2 = storeKeyFor(url2);
assert.strictEqual(key2, "api_example_com_v3_api_docs");

console.log("✅ swagger-docs storeKeyFor tests passed");
