import { run } from "./lib/python";
import { ROOT } from "./lib/root";
import path from "node:path";

run("bunx", ["pyright", "--project", path.join(ROOT, "pyrightconfig.json")]);
