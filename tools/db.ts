import { spawnSync } from "node:child_process";
import { buildPythonCommand } from "./lib/python";

const python = buildPythonCommand();
const sub = process.argv[2];

if (sub === "reset") {
  const downResult = spawnSync(python.command, [...python.args, "-m", "alembic", "downgrade", "base"], {
    stdio: "inherit", cwd: "backend", env: { ...process.env, DATABASE_URL: "" },
  });
  if (downResult.status !== 0) {
    console.error("db:reset downgrade 失败，未执行 upgrade");
    process.exit(downResult.status ?? 1);
  }
  const upResult = spawnSync(python.command, [...python.args, "-m", "alembic", "upgrade", "head"], {
    stdio: "inherit", cwd: "backend", env: { ...process.env, DATABASE_URL: "" },
  });
  if (upResult.status !== 0) {
    console.error("db:reset upgrade 失败");
    process.exit(upResult.status ?? 1);
  }
  console.log("db:reset 完成");
} else if (sub === "migrate") {
  const result = spawnSync(python.command, [...python.args, "-m", "alembic", "upgrade", "head"], {
    stdio: "inherit", cwd: "backend", env: { ...process.env, DATABASE_URL: "" },
  });
  if (result.status !== 0) {
    console.error("迁移失败");
    process.exit(result.status ?? 1);
  }
  console.log("迁移完成");
} else {
  console.error("用法: bun run tools/db.ts <reset|migrate>");
  process.exit(1);
}
