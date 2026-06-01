import { spawnSync } from "node:child_process";
import path from "node:path";
import { askForConfirmation } from "./lib/prompt";
import { buildPythonCommand, hasManagedEnvironment } from "./lib/python";

const REQUIREMENTS = path.resolve(import.meta.dir, "..", "backend", "requirements.txt");

export function installDeps(python: ReturnType<typeof buildPythonCommand>) {
  const result = spawnSync(python.command, [...python.args, "-m", "pip", "install", "-r", REQUIREMENTS], {
    stdio: "inherit",
  });
  if (result.status !== 0) {
    throw new Error(`pip install exited with code ${result.status}`);
  }
}

async function main(): Promise<void> {
  const python = buildPythonCommand();

  if (!hasManagedEnvironment() && !process.env.CI) {
    const confirmed = await askForConfirmation(
      "未检测到虚拟环境。继续安装到当前 Python 环境？[y/N] ",
    );
    if (!confirmed) process.exit(1);
  }

  installDeps(python);
}

import { fileURLToPath } from "node:url";

const isMain = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1];
if (isMain) {
  main().catch((error: unknown) => {
    console.error(error);
    process.exit(1);
  });
}
