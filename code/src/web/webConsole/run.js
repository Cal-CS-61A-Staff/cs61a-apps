import { checkArgs, resolveRelativePath } from "./utils.js";
import { getFile } from "../filesystem.js";
import { CONSOLE_EDIT } from "../../common/communicationEnums.js";
import { call } from "./webConsoleWorker.js";
import { FILE } from "../../common/fileTypes.js";

export default async function run(args, workingDirectory, out, err) {
  checkArgs("run", args, 1, 1);
  const target = resolveRelativePath(
    args[0] || workingDirectory,
    workingDirectory
  );
  const file = await getFile(target);
  if (!file || file.type !== FILE) {
    err("File not found.");
    return 1;
  }
  call(CONSOLE_EDIT, { file, startInterpreter: true });
  return 0;
}
