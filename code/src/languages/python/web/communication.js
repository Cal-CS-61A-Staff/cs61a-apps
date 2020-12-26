import $ from "jquery";
import {
  GEN_PY_TRACE,
  RUN_BLACK,
  RUN_PY_CODE,
  COMPILE_PY_FILE,
} from "../constants/communicationEnums.js";
import { err, exit, sendAndExit } from "../../../web/webBackend.js";
import { interactProcess } from "../../../main/processes.js";

import webConsole from "./web_console.py";
import runPyScript from "../../../web/runPython.js";

export default async function receive(arg) {
  if (arg.type === RUN_PY_CODE) {
    await runPyCode(arg.key, arg.code);
  } else if (arg.type === GEN_PY_TRACE) {
    const ret = await $.post("./api/pytutor", {
      code: arg.data.setup_code + arg.data.code,
    });
    const parsed = JSON.parse(ret);
    parsed.code = { main_code: parsed.code };
    sendAndExit(arg.key, JSON.stringify(parsed));
  } else if (arg.type === RUN_BLACK) {
    const ret = await $.post("./api/black", { code: arg.code });
    if (ret.success) {
      sendAndExit(arg.key, ret.code);
    } else {
      err(arg.key, ret.error);
      exit(arg.key);
    }
  } else if (arg.type === COMPILE_PY_FILE) {
    await runPyScript(arg.key, arg.code, { writeOutput: true });
  }
}

async function runPyCode(key, code) {
  await runPyScript(key, webConsole, []);
  if (code !== null) {
    interactProcess(key, code);
  }
}
