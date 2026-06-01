import { spawnSync } from "node:child_process";

spawnSync("bunx", ["pyright", "--project", "pyrightconfig.json"], {
  stdio: "inherit",
});
