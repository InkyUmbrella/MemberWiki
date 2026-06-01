import { spawnSync } from "node:child_process";
import { buildPythonCommand } from "./lib/python";
import { buildPytestArgs, parsePytestTask, TEST_TARGETS } from "./lib/pytest";

const parsed = parsePytestTask(process.argv[2]);
if (!parsed) {
  console.error("用法: bun run test");
  process.exit(1);
}

const python = buildPythonCommand();
const target = TEST_TARGETS[parsed.targetKey];
const extra = process.argv.slice(3);
const args = buildPytestArgs(target, parsed.mode, extra);
const result = spawnSync(python.command, [...python.args, ...args], {
  stdio: "inherit", cwd: "backend",
});
process.exit(result.status ?? 1);
