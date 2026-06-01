import { buildPythonCommand, run } from "./lib/python";
import { BACKEND_DIR } from "./lib/root";

const python = buildPythonCommand();
run(python.command, [...python.args, "-m", "ruff", "check", "app/", "tests/", ...process.argv.slice(2)], {
  cwd: BACKEND_DIR,
});
