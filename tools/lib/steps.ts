import { spawnSync } from "node:child_process";
import { Command, unmaskedEnv, runCheck } from "./python";
import { fail } from "./fail";
import { installDeps } from "../install";

export function updateDepsAndMigrate(python: Command, {
  updateBun = true,
  runMigrations = true,
}: { updateBun?: boolean; runMigrations?: boolean } = {}) {
  console.log("更新 Python 依赖...");
  try {
    installDeps(python);
  } catch (e) {
    fail(`pip install 失败: ${e instanceof Error ? e.message : e}`);
  }

  if (updateBun) {
    console.log("更新 bun 依赖...");
    if (!runCheck("bun", ["install"], { stdio: "inherit", shell: true as any })) {
      fail("bun install 失败");
    }
  }

  if (runMigrations) {
    console.log("运行数据库迁移...");
    const result = spawnSync(python.command, [...python.args, "-m", "alembic", "upgrade", "head"], {
      stdio: "inherit", cwd: "backend", env: unmaskedEnv(),
    });
    if (result.status !== 0) fail("数据库迁移失败", result.status ?? 1);
  }
}
