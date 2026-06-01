import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

export type Command = {
  command: string;
  args: string[];
};

export function pythonFromActiveEnvironment(): string | null {
  const condaPrefix = process.env.CONDA_PREFIX;
  if (condaPrefix) {
    const candidate =
      process.platform === "win32"
        ? path.join(condaPrefix, "python.exe")
        : path.join(condaPrefix, "bin", "python");
    if (existsSync(candidate)) {
      return candidate;
    }
  }

  const virtualEnv = process.env.VIRTUAL_ENV;
  if (virtualEnv) {
    const candidate =
      process.platform === "win32"
        ? path.join(virtualEnv, "Scripts", "python.exe")
        : path.join(virtualEnv, "bin", "python");
    if (existsSync(candidate)) {
      return candidate;
    }
  }

  return null;
}

export function fallbackPythonCommand(): Command {
  if (process.platform === "win32") {
    return { command: "py", args: ["-3"] };
  }
  return { command: "python3", args: [] };
}

export function buildPythonCommand(): Command {
  const activePython = pythonFromActiveEnvironment();
  if (activePython) {
    return { command: activePython, args: [] };
  }
  return fallbackPythonCommand();
}

export function hasManagedEnvironment(): boolean {
  return Boolean(process.env.CONDA_PREFIX || process.env.VIRTUAL_ENV);
}

export function unmaskedEnv(): Record<string, string | undefined> {
  return { ...process.env, DATABASE_URL: "" };
}

export function run(command: string, args: string[], opts?: Parameters<typeof spawnSync>[2]): void {
  const result = spawnSync(command, args, { stdio: "inherit", ...opts });
  if (result.status !== 0) process.exit(result.status ?? 1);
}

export function runCheck(command: string, args: string[], opts?: Parameters<typeof spawnSync>[2]): boolean {
  const result = spawnSync(command, args, { stdio: "inherit", ...opts });
  return result.status === 0;
}
