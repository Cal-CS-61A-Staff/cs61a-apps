import { err, exit, out } from "./webBackend.js";
import { registerProcess } from "../main/processes.js";
import {
  INDEX_QUEUE,
  INDEX_WAITING,
  NUM_POSITIONS,
  STATUS_DATA,
  STATUS_DONE,
  STATUS_FAIL,
  STATUS_READY,
} from "../common/ipcEnums.js";
import { getFile } from "./filesystem.js";
import { FILE } from "../common/fileTypes.js";

const maxStrLen = 512;
const strBuffLen = 1024;

// https://developers.google.com/web/updates/2012/06/How-to-convert-ArrayBuffer-to-and-from-String
function str2ab(strBuff, str) {
  const bufView = new Uint16Array(strBuff);
  for (let i = 0; i !== strBuffLen; ++i) {
    bufView[i] = 0;
  }
  for (let i = 0, strLen = str.length; i < strLen && i < maxStrLen; i++) {
    bufView[i] = str.charCodeAt(i);
  }
}

export default function runPyScript(key, script, args) {
  return new Promise((resolve) => {
    const worker = new Worker("/pythonWorker.js");
    const commBuff = window.SharedArrayBuffer
      ? new window.SharedArrayBuffer(4 * NUM_POSITIONS)
      : null;
    const strBuff = window.SharedArrayBuffer
      ? new window.SharedArrayBuffer(strBuffLen)
      : null;

    const getCommBuffArray = () => new Int32Array(commBuff);

    const notify = () => {
      const arr = getCommBuffArray();
      arr[INDEX_WAITING] = STATUS_READY;
      window.Atomics.notify(arr, INDEX_WAITING);
    };

    worker.postMessage({
      code: script,
      transpiled: args.transpiled,
      writeOutput: args.writeOutput,
      commBuff,
      strBuff,
    });
    worker.onmessage = () => {
      let currFile;
      let currIndex;

      worker.onmessage = async (e) => {
        if (e.data.out) {
          out(key, e.data.val);
        } else if (e.data.err) {
          err(key, e.data.val);
        } else if (e.data.exit) {
          exit(key, e.data.val);
        } else if (e.data.readFile) {
          // Atomics check already done by worker
          const file = await getFile(e.data.location);
          if (file && file.type === FILE) {
            currFile = file;
            const firstBlock = file.content.slice(0, maxStrLen);
            currIndex = maxStrLen;
            console.log("returning", firstBlock);
            str2ab(strBuff, firstBlock);
            getCommBuffArray()[INDEX_QUEUE] = STATUS_DATA;
          } else {
            getCommBuffArray()[INDEX_QUEUE] = STATUS_FAIL;
          }
          notify();
        } else if (e.data.continueReadFile) {
          // Atomics check already done by worker
          console.log("continuing...");
          if (currIndex < currFile.content.length) {
            const block = currFile.content.slice(
              currIndex,
              currIndex + maxStrLen
            );
            currIndex += maxStrLen;
            str2ab(strBuff, block);
            getCommBuffArray()[INDEX_QUEUE] = STATUS_DATA;
          } else {
            getCommBuffArray()[INDEX_QUEUE] = STATUS_DONE;
          }
          notify();
        }
      };
      registerProcess(key, {
        stdin: {
          write: (line) => {
            if (window.SharedArrayBuffer) {
              str2ab(strBuff, line);
              notify();
            }
            worker.postMessage({ input: line });
          },
        },
        kill: () => {
          try {
            worker.terminate();
          } catch {
            exit(
              key,
              "\n\nBrython web worker did not terminate correctly. " +
                "You may want to refresh the page."
            );
            return;
          }
          exit(key, "\n\nBrython web worker terminated.");
        },
      });
      resolve();
    };
  });
}
