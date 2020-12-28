import path from "path-browserify";
import { checkArgs, resolveRelativePath } from "./utils.js";
import { fileExists, storeFile } from "../filesystem.js";
import { DIRECTORY } from "../../common/fileTypes.js";

export default async function mkdir(args, workingDirectory, out, err) {
  checkArgs("mkdir", args, 1, 1);
  const target = resolveRelativePath(
    args[0] || workingDirectory,
    workingDirectory
  );
  const enclosingDirectory = path.dirname(target);
  if (!(await fileExists(enclosingDirectory))) {
    err(`Enclosing directory: ${enclosingDirectory} does not exist.`);
    return 1;
  }
  if (await fileExists(target)) {
    err(`Directory ${target} already exists.`);
    return 1;
  }
  await storeFile([], target, DIRECTORY);
  return 0;
}
