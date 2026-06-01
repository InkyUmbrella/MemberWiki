import { spawn } from "node:child_process";

const fe = spawn("bun", ["--cwd", "frontend", "run", "dev"], { stdio: "inherit", shell: true });
const be = spawn("bun", ["--cwd", "backend", "run", "dev"], { stdio: "inherit", shell: true });

function cleanup() {
  fe.kill();
  be.kill();
  process.exit();
}

process.on("SIGINT", cleanup);
process.on("SIGTERM", cleanup);
