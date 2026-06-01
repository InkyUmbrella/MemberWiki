import { buildPythonCommand, run } from "./lib/python";
import { buildPytestArgs, parsePytestTask, TEST_TARGETS } from "./lib/pytest";

const parsed = parsePytestTask(process.argv[2]);
const python = buildPythonCommand();
const target = TEST_TARGETS[parsed.targetKey];
const args = buildPytestArgs(target, parsed.mode, process.argv.slice(3));
run(python.command, [...python.args, ...args], { cwd: "backend" });
