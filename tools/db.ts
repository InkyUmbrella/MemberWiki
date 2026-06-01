import { spawnSync } from "node:child_process";
import { buildPythonCommand } from "./lib/python";

const python = buildPythonCommand();
const sub = process.argv[2];

if (sub === "reset") {
  spawnSync(python.command, [...python.args, "-m", "alembic", "downgrade", "base"], {
    stdio: "inherit", cwd: "backend", env: { ...process.env, DATABASE_URL: "" },
  });
  spawnSync(python.command, [...python.args, "-m", "alembic", "upgrade", "head"], {
    stdio: "inherit", cwd: "backend", env: { ...process.env, DATABASE_URL: "" },
  });
  console.log("✅ db:reset 完成");
} else if (sub === "migrate") {
  spawnSync(python.command, [...python.args, "-m", "alembic", "upgrade", "head"], {
    stdio: "inherit", cwd: "backend", env: { ...process.env, DATABASE_URL: "" },
  });
  console.log("✅ 迁移完成");
} else {
  console.error("用法: bun run tools/db.ts <reset|migrate>");
  process.exit(1);
}
