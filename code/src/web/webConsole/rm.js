import { checkArgs, resolveRelativePath } from "./utils.js";
import { getFile, removeFile } from "../filesystem.js";
import { DIRECTORY } from "../../common/fileTypes.js";

export default async function rm(args, workingDirectory, out, err) {
  checkArgs("rm", args, 1, 1);
  const target = resolveRelativePath(
    args[0] || workingDirectory,
    workingDirectory
  );
  const file = await getFile(target);
  if (!file) {
    err(`File ${target} does not exist`);
    return 1;
  }

  if (file.type === DIRECTORY && file.content.length !== 0) {
    err(`Directory ${target} is not empty.`);
    return 1;
  }
  await removeFile(target);
  return 0;
}
