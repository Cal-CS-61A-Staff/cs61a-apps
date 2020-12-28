import * as temp from "temp";
import fs from "fs";
import runPyScript from "../../main/runPython.js";
import {
  FORMAT,
  GEN_SCM_TRACE,
  RUN_SCM_CODE,
  RUN_SCM_FILE,
} from "./constants/communicationEnums.js";

export default function receive(arg) {
  if (arg.type === RUN_SCM_CODE) {
    runScmCode(arg.key, arg.code);
  } else if (arg.type === RUN_SCM_FILE) {
    runPyScript(arg.key, `${__static}/scheme/scheme`, [], [arg.location, "-i"]);
  } else if (arg.type === FORMAT) {
    scmFormat(arg.key, arg.code);
  } else if (arg.type === GEN_SCM_TRACE) {
    scmDebug(arg.key, arg.code); // setup_code, working_directory need to be handled!
  }
}

function runScmCode(key, code) {
  temp.open("scmTempFile", (fail, info) => {
    if (!fail) {
      fs.write(info.fd, code, () => {
        fs.close(info.fd, () => null);
        runPyScript(key, `${__static}/scheme/scheme`, [], [info.path, "-i"]);
      });
    }
  });
}

function scmDebug(key, code) {
  temp.open("scmTempFile", (fail, info) => {
    if (!fail) {
      fs.write(info.fd, code, () => {
        fs.close(info.fd, () => null);
        runPyScript(
          key,
          `${__static}/scheme/scheme`,
          [],
          ["-debug", info.path]
        );
      });
    }
  });
}

function scmFormat(key, code) {
  temp.open("scmTempFile", (fail, info) => {
    if (!fail) {
      fs.write(info.fd, code, () => {
        fs.close(info.fd, () => null);
        runPyScript(
          key,
          `${__static}/scheme/formatter`,
          [],
          ["--reformat", info.path]
        );
      });
    }
  });
}
