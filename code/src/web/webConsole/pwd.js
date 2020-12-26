import { checkArgs, resolveRelativePath } from "./utils.js";

export default async function pwd(args, workingDirectory, out) {
  checkArgs("pwd", args, 0, 0);
  const target = resolveRelativePath(
    args[0] || workingDirectory,
    workingDirectory
  );
  out(target);
  return 0;
}
