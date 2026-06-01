import { existsSync, mkdirSync, unlinkSync, writeFileSync } from "node:fs";
import path from "node:path";

export type TestMode = "test" | "cov";

export type TestTarget = {
  path?: string;
};

export const TEST_TARGETS: Record<string, TestTarget> = {
  all: {},
};

function isDirectoryWritable(directory: string): boolean {
  try {
    mkdirSync(directory, { recursive: true });
    const probePath = path.join(directory, ".bun-pytest-probe");
    writeFileSync(probePath, "probe");
    unlinkSync(probePath);
    return true;
  } catch {
    return false;
  }
}

export function resolvePytestCacheDir(cwd: string = process.cwd()): string {
  const primaryCacheDir = path.join(cwd, "tmp", "pytest-cache");
  if (isDirectoryWritable(primaryCacheDir)) {
    return primaryCacheDir;
  }

  // 主缓存目录不可写时，退回到仓库内独立隐藏目录，保持缓存能力
  const fallbackCacheDir = path.join(cwd, ".cache", "pytest");
  mkdirSync(fallbackCacheDir, { recursive: true });
  return fallbackCacheDir;
}

export function buildPytestArgs(target: TestTarget, mode: TestMode, extraArgs: string[] = []): string[] {
  const args = ["-m", "pytest", "-o", `cache_dir=${resolvePytestCacheDir()}`];

  if (target.path) {
    args.push(target.path);
  }

  args.push(...extraArgs);

  return args;
}

export function parsePytestTask(rawTask?: string): { mode: TestMode; targetKey: string } {
  if (!rawTask) {
    return { mode: "test", targetKey: "all" };
  }

  const [mode, targetKey = "all"] = rawTask.split(":");
  if ((mode !== "test" && mode !== "cov") || !(targetKey in TEST_TARGETS)) {
    return { mode: "test", targetKey: "all" };
  }

  return { mode, targetKey };
}
