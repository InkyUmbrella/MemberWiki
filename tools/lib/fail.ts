export function fail(msg: string, code: number = 1): never {
  console.error(msg);
  process.exit(code);
}
