import { err, exit, out } from "./webBackend.js";
import { registerProcess } from "../main/processes.js";

export default function startConsole(key) {
  const worker = new Worker("webConsoleWorker.js");
  worker.onmessage = (e) => {
    if (e.data.out) {
      out(key, e.data.val);
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
          "\n\nConsole web worker did not terminate correctly. " +
            "You may want to refresh the page."
        );
        return;
      }
      exit(key, "\n\nConsole web worker terminated.");
    },
  });
}
