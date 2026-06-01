import { existsSync, copyFileSync, mkdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { buildPythonCommand, hasManagedEnvironment } from "./lib/python";
import { askForConfirmation } from "./lib/prompt";
import { installDeps } from "./install";

const TEMPLATES = [
  { src: ".env.example", dest: ".env" },
  { src: "backend/.env.example", dest: "backend/.env" },
  { src: "backend/alembic.ini.example", dest: "backend/alembic.ini" },
];

async function main() {
  const python = buildPythonCommand();

  if (!hasManagedEnvironment() && !process.env.CI) {
    console.log("警告: 未检测到虚拟环境");
    const ok = await askForConfirmation("在没有虚拟环境的情况下继续初始化？[y/N] ");
    if (!ok) process.exit(1);
  }

  for (const { src, dest } of TEMPLATES) {
    if (existsSync(dest)) {
      const ok = await askForConfirmation(`${dest} 已存在，覆盖？[y/N] `);
      if (!ok) { console.log(`  跳过 ${dest}`); continue; }
    }
    copyFileSync(src, dest);
    console.log(`  ${dest}`);
  }

  const dataDir = "backend/data";
  if (!existsSync(dataDir)) {
    mkdirSync(dataDir, { recursive: true });
    console.log(`  ${dataDir}/`);
  }

  console.log("\n安装 Python 依赖...");
  try {
    installDeps(python);
  } catch (e) {
    console.error("pip install 失败:", e instanceof Error ? e.message : e);
    process.exit(1);
  }

  console.log("安装 bun 依赖...");
  const bunResult = spawnSync("bun", ["install"], { stdio: "inherit", shell: true });
  if (bunResult.status !== 0) {
    console.error("bun install 失败");
    process.exit(bunResult.status ?? 1);
  }

  console.log("运行数据库迁移...");
  const alembicResult = spawnSync(python.command, [...python.args, "-m", "alembic", "upgrade", "head"], {
    stdio: "inherit", cwd: "backend", env: { ...process.env, DATABASE_URL: "" },
  });
  if (alembicResult.status !== 0) {
    console.error("数据库迁移失败");
    process.exit(alembicResult.status ?? 1);
  }

  console.log("\nMemberWiki 开发环境就绪！");
  console.log("   bun run dev     启动前后端");
  console.log("   bun run test    运行测试");
  console.log("   bun run update  更新依赖+迁移");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
