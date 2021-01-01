import { RUN_SQL_CODE } from "../constants/communicationEnums.js";
import { err, exit, out } from "../../../web/webBackend.js";
import { interactProcess, registerProcess } from "../../../main/processes.js";

import "../sqlStyle.css";

export default async function receive(arg) {
  if (arg.type === RUN_SQL_CODE) {
    runSqlCode(arg.key, arg.code);
  }
}

async function runSqlCode(key, code) {
  const worker = new Worker("/sqlWorker.js");
  worker.onmessage = (e) => {
    if (e.data.out) {
      out(key, {
        __html: e.data.val,
        visualization: e.data.visualization,
        startsWith: (...x) => (e.data.val || "").startsWith(...x),
        substr: (...x) => (e.data.val || "").substr(...x),
      });
    } else if (e.data.error) {
      err(key, e.data.val);
    } else if (e.data.exit) {
      exit(key, e.data.val);
    } else if (e.data.call) {
      out(key, { cmd: e.data.cmd, data: e.data.data });
    }
  };
  registerProcess(key, {
    stdin: {
      write: (line) => worker.postMessage({ input: line }),
    },
    kill: () => {
      try {
        worker.terminate();
      } catch {
        exit(
          key,
          "\n\nSQL web worker did not terminate correctly. " +
            "You may want to refresh the page."
        );
        return;
      }
      exit(key, "\n\nSQL web worker terminated.");
    },
  });
  if (code !== null) {
    interactProcess(key, code);
  }
}
