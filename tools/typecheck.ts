import { run } from "./lib/python";

run("bunx", ["pyright", "--project", "pyrightconfig.json"]);
