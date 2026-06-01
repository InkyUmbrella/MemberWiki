import { existsSync, rmSync } from "node:fs";
import { join } from "node:path";

const TO_REMOVE = [
  ".env",
  "backend/.env",
  "backend/alembic.ini",
  "backend/data",
  "node_modules",
  "frontend/node_modules",
  "backend/node_modules",
];

let count = 0;
for (const path of TO_REMOVE) {
  if (existsSync(path)) {
    rmSync(path, { recursive: true, force: true });
    console.log(`  ${path}`);
    count++;
  }
}
console.log(`已清除 ${count} 个文件/目录 (可重新运行 bun setup)`);
