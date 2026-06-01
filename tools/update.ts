import { spawnSync } from "node:child_process";
import { buildPythonCommand } from "./lib/python";
import { installDeps } from "./install";

const python = buildPythonCommand();

console.log("更新 Python 依赖...");
try {
  installDeps(python);
} catch (e) {
  console.error("pip install 失败:", e instanceof Error ? e.message : e);
  process.exit(1);
}

console.log("更新 bun 依赖...");
const bunResult = spawnSync("bun", ["install"], { stdio: "inherit", shell: true });
if (bunResult.status !== 0) {
  console.error("bun install 失败");
  process.exit(bunResult.status ?? 1);
}

console.log("运行数据库迁移...");
const alembicResult = spawnSync(python.command, [...python.args, "-m", "alembic", "upgrade", "head"], {
  stdio: "inherit", cwd: "backend", env: { ...process.env, DATABASE_URL: "" },
});
if (alembicResult.status !== 0) {
  console.error("数据库迁移失败");
  process.exit(alembicResult.status ?? 1);
}

console.log("\n依赖已更新，数据库已迁移");
