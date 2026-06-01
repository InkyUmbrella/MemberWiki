import { runCheck, buildPythonCommand, run, unmaskedEnv } from "./lib/python";
import { fail } from "./lib/fail";

const python = buildPythonCommand();
const sub = process.argv[2];

if (sub === "reset") {
  if (!runCheck(python.command, [...python.args, "-m", "alembic", "downgrade", "base"], {
    cwd: "backend", env: unmaskedEnv(),
  })) {
    fail("downgrade 失败，未执行 upgrade");
  }
  run(python.command, [...python.args, "-m", "alembic", "upgrade", "head"], {
    cwd: "backend", env: unmaskedEnv(),
  });
  console.log("db:reset 完成");
} else if (sub === "migrate") {
  run(python.command, [...python.args, "-m", "alembic", "upgrade", "head"], {
    cwd: "backend", env: unmaskedEnv(),
  });
  console.log("迁移完成");
} else {
  fail("用法: bun run tools/db.ts <reset|migrate>");
}
