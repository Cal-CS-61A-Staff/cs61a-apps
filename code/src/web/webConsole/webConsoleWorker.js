import splitCommand from "./tokenize.js";
import help from "./help.js";
import ls from "./ls.js";
import cd from "./cd.js";
import mkdir from "./mkdir.js";
import rm from "./rm.js";
import cat from "./cat.js";
import edit from "./edit.js";
import run from "./run.js";

import { normalize } from "../filesystem.js";
import pwd from "./pwd.js";
import post from "../../common/post.js";

let location = "~";

let username = null;

export function changeDirectory(newLocation) {
  const normalized = normalize(newLocation);
  if (normalized.startsWith("/home")) {
    location = normalize(`~/${normalized.slice(5)}`);
  } else {
    location = normalize(normalized);
  }
}

export function call(cmd, data) {
  postMessage({ call: true, cmd, data });
}

function stdout(val) {
  postMessage({ out: true, val });
}

function stderr(val) {
  postMessage({ error: true, val });
}

// eslint-disable-next-line no-unused-vars
function exit(val) {
  postMessage({ exit: true, val });
}

post("/api/user")
  .then(({ data: { email } }) => {
    [username] = email.split("@");
  })
  .catch(() => {
    username = "anonymous";
  })
  .then(() => stderr(genPrompt()));

const COMMANDS = {
  help,
  ls,
  cd,
  mkdir,
  rm,
  cat,
  edit,
  run,
  pwd,
};

onmessage = async (e) => {
  const { data } = e;
  const { input } = data;
  let commandName;
  let args;
  try {
    [commandName, ...args] = splitCommand(input);
  } catch (err) {
    stderr(`Parse failed with error: ${err.message}\n`);
  }
  if (commandName) {
    const command = COMMANDS[commandName];
    if (command) {
      try {
        await COMMANDS[commandName](args, location, stdout, stderr);
      } catch (err) {
        stderr(`${err.message}\n`);
      }
    } else {
      stderr(`Command ${commandName} was not found\n`);
    }
  }
  stdout("\n");
  stderr(genPrompt());
};

function genPrompt() {
  return `${username} ${location} $ `;
}
