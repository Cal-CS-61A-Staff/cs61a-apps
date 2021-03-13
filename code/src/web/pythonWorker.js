/* eslint-disable no-restricted-globals */
import { join } from "path";
import {
  STATUS_WAITING,
  INDEX_WAITING,
  INDEX_QUEUE,
  STATUS_DATA,
  STATUS_DONE,
  STATUS_FAIL,
} from "../common/ipcEnums.js";

self.window = self;
// eslint-disable-next-line func-names
self.Node = function () {}; // stub needed for webworker

importScripts(join(__static, "brython/brython.js"));
importScripts(join(__static, "brython/brython_stdlib.js"));

let code = false;
let commBuff;
let strBuff;

onmessage = async (e) => {
  const { data } = e;
  if (code) {
    handleInput(data.input);
  } else {
    ({ code, commBuff, strBuff } = data);
    const { transpiled, writeOutput } = data;
    initialize();
    await doBackgroundTasks();
    if (transpiled) {
      initializeTranspiledJS();
    } else {
      initializePython(writeOutput);
    }
  }
};

function doBackgroundTasks() {
  return new Promise((resolve) => {
    setTimeout(resolve, 0);
  });
}

// https://developers.google.com/web/updates/2012/06/How-to-convert-ArrayBuffer-to-and-from-String
function ab2str(buf) {
  const out = [];
  const arr = new Uint16Array(buf);
  for (let i = 0; i !== 1024; ++i) {
    if (arr[i] === 0) {
      break;
    }
    out.push(String.fromCharCode(arr[i]));
  }
  return out.join("");
}

function blockingInput(message) {
  if (self.Atomics) {
    wait();
    return ab2str(strBuff);
  } else {
    throw Error(message);
  }
}

function wait() {
  const arr = new Int32Array(commBuff);
  self.Atomics.wait(arr, INDEX_WAITING, STATUS_WAITING);
  arr[INDEX_WAITING] = STATUS_WAITING;
  return true;
}

function read(location) {
  if (!self.Atomics) {
    throw Error(
      "Your browser does not support synchronous imports. Try using Chrome instead!"
    );
  }
  postMessage({ readFile: true, location });
  const arr = new Int32Array(commBuff);
  const data = [];
  while (wait()) {
    const status = arr[INDEX_QUEUE];
    if (status === STATUS_DATA) {
      data.push(ab2str(strBuff));
    } else if (status === STATUS_DONE) {
      break;
    } else if (status === STATUS_FAIL) {
      throw Error("File not found!");
    }
    postMessage({ continueReadFile: true });
  }
  return data.join("");
}

let handler;

function initialize() {
  self.stdin = {
    on: (pyHandler) => {
      handler = pyHandler;
      postMessage("ready!");
    },
  };
  self.stdout = { write: (val) => postMessage({ out: true, val }) };
  self.stderr = { write: (val) => postMessage({ err: true, val }) };
  self.exit = { write: (val) => postMessage({ exit: true, val }) };
  self.filesystem = { read };
  self.blockingInput = { wait: blockingInput };
  __BRYTHON__.brython();
  __BRYTHON__.idb_open();
  __BRYTHON__.brython_path = "/static/brython/";
}

function initializePython(writeOutput) {
  if (writeOutput) {
    postMessage("ready!");
    setTimeout(
      () => postMessage({ out: true, val: __BRYTHON__.python_to_js(code) }),
      100
    );
  } else {
    __BRYTHON__.run_script(code, "__main__", "https://code.cs61a.org/__main__");
  }
}

function initializeTranspiledJS() {
  // eslint-disable-next-line no-eval
  (0, eval)(code);
}

function handleInput(data) {
  if (self.Atomics) {
    const arr = new Int32Array(commBuff);
    if (arr[0] !== 0) {
      arr[0] = 0;
      handler(data);
    }
  } else {
    handler(data);
  }
}
