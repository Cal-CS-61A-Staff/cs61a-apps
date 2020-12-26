import serverSocket from "net";
import { exit, out } from "./communication";

let handler = null;

function createSocketListener(PORT, HOST) {
  serverSocket
    .createServer((socket) => {
      let buffer = "";
      socket.on("data", (data) => {
        buffer = data;
      });
      socket.on("close", () => {
        const parsedData = JSON.parse(buffer);
        if (handler !== null) {
          out(handler, parsedData);
        }
      });
    })
    .listen(PORT, HOST);
}

export function registerOKPyHandler(key) {
  if (handler !== null) {
    exit(handler);
  }
  handler = key;
}

export function startOkServer() {
  createSocketListener(31415, "localhost");
}
