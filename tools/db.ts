import { runCheck, buildPythonCommand, run, unmaskedEnv } from "./lib/python";
import { BACKEND_DIR } from "./lib/root";
import { fail } from "./lib/fail";

export function resetDb(): void {
  const python = buildPythonCommand();
  if (!runCheck(python.command, [...python.args, "-m", "alembic", "downgrade", "base"], {
    cwd: BACKEND_DIR, env: unmaskedEnv(),
  })) {
    fail("downgrade 失败，未执行 upgrade");
  }
  run(python.command, [...python.args, "-m", "alembic", "upgrade", "head"], {
    cwd: BACKEND_DIR, env: unmaskedEnv(),
  });
  console.log("  db:reset 完成");
}

export function migrateDb(): void {
  const python = buildPythonCommand();
  run(python.command, [...python.args, "-m", "alembic", "upgrade", "head"], {
    cwd: BACKEND_DIR, env: unmaskedEnv(),
  });
  console.log("  迁移完成");
}

if (import.meta.main) {
  const sub = process.argv[2];

  if (sub === "reset") {
    resetDb();
  } else if (sub === "migrate") {
    migrateDb();
  } else {
    fail("用法: bun run tools/db.ts <reset|migrate>");
  }
}
