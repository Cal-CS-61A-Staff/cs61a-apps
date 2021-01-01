import * as temp from "temp";
import fs from "fs";
import runPyScript from "../../main/runPython.js";
import {
  GEN_PY_TRACE,
  RUN_BLACK,
  RUN_PY_CODE,
  RUN_PY_FILE,
} from "./constants/communicationEnums.js";

export function runPyCode(key, code) {
  temp.open("pythonTempFile", (fail, info) => {
    if (!fail) {
      fs.write(info.fd, code, () => {
        fs.close(info.fd, () => null);
        runPyScript(key, info.path, ["-i"], []);
      });
    }
  });
}

export default async function receive(arg) {
  if (arg.type === RUN_PY_CODE) {
    runPyCode(arg.key, arg.code);
  } else if (arg.type === RUN_PY_FILE) {
    runPyScript(arg.key, arg.location, ["-i"], []);
  } else if (arg.type === GEN_PY_TRACE) {
    runPyScript(
      arg.key,
      `${__static}/python/wrapper.py`,
      [],
      [JSON.stringify(arg.data)]
    );
  } else if (arg.type === RUN_BLACK) {
    runPyScript(arg.key, `${__static}/python/black`, [], ["--code", arg.code]);
  }
}
