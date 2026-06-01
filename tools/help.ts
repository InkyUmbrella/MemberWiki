console.log(`MemberWiki 开发命令:

  bun run setup     首次克隆后全流程初始化
  bun run dev       同时启动前端(5173)+后端(8000)
  bun run test      运行全量测试
  bun run lint      代码检查 (eslint + ruff)
  bun run typecheck 类型检查 (tsc + pyright)
  bun run update    更新依赖 + 数据库迁移
  bun run db:reset  重建数据库
  bun run clean     清除本地生成文件
  bun run help      显示此帮助`);
