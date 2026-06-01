import { spawnSync } from "node:child_process";

const result = spawnSync("bunx", ["pyright", "--project", "pyrightconfig.json"], {
  stdio: "inherit",
});
process.exit(result.status ?? 1);
