import { readFileSync, existsSync, readdirSync, unlinkSync, watchFile, statSync } from "node:fs";
import { join, basename } from "node:path";
import { BACKEND_DIR } from "./lib/root";
import { fail } from "./lib/fail";

const LOGS_DIR = join(BACKEND_DIR, "logs");

function getLatestLogFile(): string | null {
  if (!existsSync(LOGS_DIR)) return null;
  const files = readdirSync(LOGS_DIR)
    .filter(f => f.endsWith(".jsonl"))
    .map(f => ({ name: f, mtime: statSync(join(LOGS_DIR, f)).mtimeMs }))
    .sort((a, b) => b.mtime - a.mtime);
  return files.length > 0 ? join(LOGS_DIR, files[0].name) : null;
}

interface LogEntry {
  timestamp: string;
  level: string;
  logger: string;
  message: string;
  request_id: string;
  elapsed?: number;
  exception?: string;
}

function parseLine(line: string): LogEntry | null {
  try {
    return JSON.parse(line);
  } catch {
    return null;
  }
}

function formatEntry(e: LogEntry): string {
  const ts = e.timestamp.slice(0, 19).replace("T", " ");
  const level = e.level.padEnd(5);
  const logger = e.logger.split(".").slice(-2).join(".").padEnd(28);
  const elapsed = e.elapsed ? `  ${e.elapsed.toFixed(3)}s` : "";
  let line = `${ts}  ${level}  ${logger}  ${e.message}${elapsed}`;
  if (e.exception) {
    const firstLine = e.exception.split("\n")[0] || "";
    line += `\n         --> ${firstLine}`;
  }
  return line;
}

function showTail(lines: number = 50): void {
  const file = getLatestLogFile();
  if (!file) fail("未找到日志文件");
  const content = readFileSync(file, "utf-8");
  const all = content.trim().split("\n").filter(Boolean);
  const tail = all.slice(-lines);
  for (const line of tail) {
    const entry = parseLine(line);
    if (entry) console.log(formatEntry(entry));
    else console.log(line);
  }
}

function showFollow(): void {
  const file = getLatestLogFile();
  if (!file) fail("未找到日志文件");
  let lastSize = statSync(file).size;
  console.log(`跟踪 ${basename(file)} (Ctrl+C 退出)`);

  watchFile(file, { interval: 500 }, () => {
    const cur = statSync(file);
    if (cur.size > lastSize) {
      const stream = readFileSync(file, { encoding: "utf-8" });
      const newContent = stream.slice(lastSize);
      for (const line of newContent.trim().split("\n").filter(Boolean)) {
        const entry = parseLine(line);
        if (entry) console.log(formatEntry(entry));
        else console.log(line);
      }
      lastSize = cur.size;
    }
    if (cur.size < lastSize) {
      console.log("(日志文件被截断)");
      lastSize = 0;
    }
  });
}

function showSearch(query: string): void {
  const file = getLatestLogFile();
  if (!file) fail("未找到日志文件");
  const content = readFileSync(file, "utf-8");
  const lowerQ = query.toLowerCase();
  let count = 0;
  for (const line of content.trim().split("\n").filter(Boolean)) {
    const entry = parseLine(line);
    if (!entry) continue;
    const searchable = `${entry.level} ${entry.logger} ${entry.message} ${entry.exception || ""}`.toLowerCase();
    if (searchable.includes(lowerQ)) {
      console.log(formatEntry(entry));
      count++;
    }
  }
  console.log(`\n匹配 ${count} 条`);
}

export function cleanLogs(): void {
  if (!existsSync(LOGS_DIR)) return;
  let count = 0;
  for (const entry of readdirSync(LOGS_DIR)) {
    if (entry.endsWith(".jsonl")) {
      unlinkSync(join(LOGS_DIR, entry));
      count++;
    }
  }
  console.log(`  logs: 清除 ${count} 个日志文件`);
}

if (import.meta.main) {
  const arg = process.argv[2];

  if (!arg || arg === "tail") {
    showTail();
  } else if (arg === "-f" || arg === "--follow" || arg === "--tail") {
    showFollow();
  } else if (arg === "--search" || arg === "-s") {
    const query = process.argv[3];
    if (!query) fail("用法: bun run tools/logs.ts --search <关键词>");
    showSearch(query);
  } else if (arg === "--clean") {
    cleanLogs();
  } else {
    fail("用法: bun run tools/logs.ts [tail|--tail/-f|--search/-s <q>|--clean]");
  }
}
