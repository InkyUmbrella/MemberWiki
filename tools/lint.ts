import { buildPythonCommand, run } from "./lib/python";

const python = buildPythonCommand();
run(python.command, [...python.args, "-m", "ruff", "check", "app/", "tests/", ...process.argv.slice(2)], {
  cwd: "backend",
});
