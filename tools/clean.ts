import { existsSync, rmSync } from "node:fs";
import { join } from "node:path";
import { BACKEND_DIR, ROOT } from "./lib/root";
import { resetDb } from "./db";
import { cleanLogs } from "./logs";
import { fail } from "./lib/fail";

function cleanAll(): void {
  cleanCache();
  cleanLogs();
  resetDb();

  const toRemove = [
    ".env",
    "backend/.env",
    "backend/alembic.ini",
    "backend/data",
    "node_modules",
    "frontend/node_modules",
    "backend/node_modules",
  ];
  let count = 0;
  for (const path of toRemove) {
    if (existsSync(path)) {
      rmSync(path, { recursive: true, force: true });
      console.log(`  ${path}`);
      count++;
    }
  }
  console.log(`  项目文件: 清除 ${count} 个 (可重新运行 bun setup)`);
}

const sub = process.argv[2] || "all";

switch (sub) {
  case "all":
    cleanAll();
    break;
  case "cache":
    cleanCache();
    break;
  default:
    fail(`用法: bun run tools/clean.ts <all|cache>`);
}
