import { existsSync, copyFileSync, mkdirSync } from "node:fs";
import { buildPythonCommand, hasManagedEnvironment } from "./lib/python";
import { askForConfirmation } from "./lib/prompt";
import { updateDepsAndMigrate } from "./lib/steps";

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

  console.log("");
  updateDepsAndMigrate(python);

  console.log("\nMemberWiki 开发环境就绪！");
  console.log("   bun run dev     启动前后端");
  console.log("   bun run test    运行测试");
  console.log("   bun run update  更新依赖+迁移");
  console.log("   bun run help    查看所有命令");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
