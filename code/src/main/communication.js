// eslint-disable-next-line import/no-extraneous-dependencies
import { ipcMain } from "electron";

import { interactProcess, killProcess } from "./processes";
import { save, open, showOpenDialog, showSaveDialog } from "./filesystem";
import {
  INTERACT_PROCESS,
  KILL_PROCESS,
  SHOW_OPEN_DIALOG,
  SHOW_SAVE_DIALOG,
  OUT,
  ERR,
  EXIT,
  CLAIM_MENU,
  SAVE_FILE,
  REGISTER_OKPY_HANDLER,
  REQUEST_KEY,
  OPEN_FILE,
} from "../common/communicationEnums.js";

import python from "../languages/python/communication";
import scheme from "../languages/scheme/communication";
import { assignMenuKey } from "./initializeMenu";
import { registerOKPyHandler } from "./ok_interface";
import { PYTHON, SCHEME } from "../common/languages.js";

const senders = {};

let nextKey = 0;

export function addHandlers() {
  ipcMain.on("asynchronous-message", (event, arg) => {
    senders[arg.key] = event.sender;
    receive(arg);
  });

  ipcMain.on("synchronous-message", (event, arg) => {
    if (arg === REQUEST_KEY) {
      // eslint-disable-next-line no-param-reassign
      event.returnValue = nextKey++;
    } else {
      console.error("Unknown synchronous request:", arg);
    }
  });
}

function receive(arg) {
  console.log("Receive", arg);
  if (!arg.handler) {
    // main server handler
    if (arg.type === INTERACT_PROCESS) {
      interactProcess(arg.key, arg.line);
    } else if (arg.type === KILL_PROCESS) {
      killProcess(arg.key);
    } else if (arg.type === SHOW_OPEN_DIALOG) {
      showOpenDialog(arg.key);
    } else if (arg.type === OPEN_FILE) {
      open(arg.key, arg.location);
    } else if (arg.type === SHOW_SAVE_DIALOG) {
      showSaveDialog(arg.key, arg.contents, arg.hint);
    } else if (arg.type === SAVE_FILE) {
      save(arg.key, arg.contents, arg.location);
    } else if (arg.type === CLAIM_MENU) {
      assignMenuKey(arg.key);
    } else if (arg.type === REGISTER_OKPY_HANDLER) {
      registerOKPyHandler(arg.key, arg.fileName);
    } else {
      console.error(`Unknown (or missing) type: ${arg.type}`);
    }
  } else if (arg.handler === PYTHON) {
    python(arg);
  } else if (arg.handler === SCHEME) {
    scheme(arg);
  } else {
    console.error(`Unknown handler: ${arg.handler}`);
  }
}

export function send(arg) {
  console.log("Send", arg);
  try {
    senders[arg.key].send("asynchronous-reply", arg);
  } catch (e) {
    console.error(e);
    delete senders[arg.key];
  }
}

export function out(key, val) {
  send({ key, type: OUT, out: val });
}

export function err(key, val) {
  send({ key, type: ERR, out: val });
}

export function exit(key, val) {
  send({ key, type: EXIT, out: val });
}

export function sendAndExit(key, msg) {
  out(key, msg);
  exit(key);
}
