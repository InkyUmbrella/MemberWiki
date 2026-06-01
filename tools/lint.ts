import { spawnSync } from "node:child_process";
import { buildPythonCommand } from "./lib/python";

const python = buildPythonCommand();
const extra = process.argv.slice(2);
spawnSync(python.command, [...python.args, "-m", "ruff", "check", "app/", "tests/", ...extra], {
  stdio: "inherit", cwd: "backend",
});
