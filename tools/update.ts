import { spawnSync } from "node:child_process";
import { buildPythonCommand } from "./lib/python";
import { installDeps } from "./install";

const python = buildPythonCommand();

console.log("📦 更新 Python 依赖...");
installDeps(python);

console.log("📦 更新 bun 依赖...");
spawnSync("bun", ["install"], { stdio: "inherit", shell: true });

console.log("🗄️  运行数据库迁移...");
spawnSync(python.command, [...python.args, "-m", "alembic", "upgrade", "head"], {
  stdio: "inherit", cwd: "backend", env: { ...process.env, DATABASE_URL: "" },
});

console.log("\n✅ 依赖已更新，数据库已迁移");
