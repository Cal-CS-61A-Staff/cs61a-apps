import { checkArgs, resolveRelativePath } from "./utils.js";
import { getFile } from "../filesystem.js";
import { changeDirectory } from "./webConsoleWorker.js";
import { DIRECTORY } from "../../common/fileTypes.js";

export default async function cd(args, workingDirectory, out, err) {
  checkArgs("cd", args, 1, 1);
  const target = resolveRelativePath(
    args[0] || workingDirectory,
    workingDirectory
  );
  const folder = await getFile(target);
  if (!folder || folder.type !== DIRECTORY) {
    err("Directory not found.");
    return 1;
  }
  changeDirectory(target);
  return 0;
}
