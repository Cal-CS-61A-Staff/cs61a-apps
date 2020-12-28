// eslint-disable-next-line
import { dialog } from "electron";
import { basename } from "path";

import { readFile, writeFile } from "fs";
import { sendAndExit } from "./communication";

export function showOpenDialog(key) {
  dialog.showOpenDialog({}, (filePaths) => {
    if (filePaths) {
      open(key, filePaths[0]);
    } else {
      sendAndExit(key, { success: false });
    }
  });
}

export function open(key, location) {
  readFile(location, (error, data) => {
    if (error) {
      sendAndExit(key, { success: false });
    } else {
      const content = data.toString("utf-8");
      sendAndExit(key, {
        success: true,
        file: {
          name: basename(location),
          location,
          content,
        },
      });
    }
  });
}

// TODO: take the hint! (xD)
// eslint-disable-next-line
export function showSaveDialog(key, contents, hint) {
  dialog.showSaveDialog({}, (location) => {
    if (location) {
      save(key, contents, location);
    } else {
      sendAndExit(key, { success: false });
    }
  });
}

export function save(key, contents, location) {
  writeFile(location, contents, (error) => {
    if (error) {
      sendAndExit(key, { success: false });
    } else {
      sendAndExit(key, { success: true, name: basename(location), location });
    }
  });
}
