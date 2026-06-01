import { buildPythonCommand, runCheck, unmaskedEnv } from "./lib/python";
import { fail } from "./lib/fail";
import { installDeps } from "./install";

const python = buildPythonCommand();

console.log("更新 Python 依赖...");
try {
  installDeps(python);
} catch (e) {
  fail(`pip install 失败: ${e instanceof Error ? e.message : e}`);
}

console.log("更新 bun 依赖...");
if (!runCheck("bun", ["install"], { shell: true })) {
  fail("bun install 失败");
}

console.log("运行数据库迁移...");
if (!runCheck(python.command, [...python.args, "-m", "alembic", "upgrade", "head"], {
  cwd: "backend", env: unmaskedEnv(),
})) {
  fail("数据库迁移失败");
}

console.log("\n依赖已更新，数据库已迁移");
