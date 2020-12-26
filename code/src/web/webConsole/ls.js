import path from "path-browserify";
import { checkArgs, resolveRelativePath } from "./utils.js";
import { getFile } from "../filesystem.js";
import { DIRECTORY } from "../../common/fileTypes.js";

export default async function ls(args, workingDirectory, out, err) {
  checkArgs("ls", args, 0, 1);
  const target = resolveRelativePath(
    args[0] || workingDirectory,
    workingDirectory
  );
  const folder = await getFile(target);
  if (!folder || folder.type !== DIRECTORY) {
    err("Directory not found.");
    return 1;
  }
  for (const file of folder.content) {
    out(`${path.basename(file)}\n`);
  }
  return 0;
}
