// eslint-disable-next-line import/no-extraneous-dependencies
import { app, Menu } from "electron";
import { exit, out } from "./communication";
import {
  MENU_CLOSE_TAB,
  MENU_NEW,
  MENU_OPEN,
  MENU_SAVE,
  MENU_SAVE_AS,
} from "../common/communicationEnums.js";
import { closeActiveWindow, createWindow, windows } from "./index.js";

let menuKey = null;

export function assignMenuKey(key) {
  if (menuKey) {
    exit(menuKey);
  }
  menuKey = key;
}

export function initializeMenu() {
  const isMac = process.platform === "darwin";

  const template = [
    // { role: 'appMenu' }
    ...(isMac
      ? [
          {
            label: "61A Editor",
            submenu: [
              { role: "about" },
              { type: "separator" },
              { role: "services" },
              { type: "separator" },
              { role: "hide" },
              { role: "hideothers" },
              { role: "unhide" },
              { type: "separator" },
              {
                label: "Quit 61A Editor",
                accelerator: "Cmd+Q",
                click: () => setTimeout(() => app.quit(), 0),
              },
            ],
          },
        ]
      : []),
    // { role: 'fileMenu' }
    {
      label: "File",
      submenu: [
        { label: "New File", accelerator: "CmdOrCtrl+N", click: newClick },
        {
          label: "New Window",
          accelerator: "CmdOrCtrl+Shift+N",
          click: createWindow,
        },
        { label: "Open", accelerator: "CmdOrCtrl+O", click: openClick },
        { type: "separator" },
        { label: "Save", accelerator: "CmdOrCtrl+S", click: saveClick },
        {
          label: "Save As",
          accelerator: "Shift+CmdOrCtrl+S",
          click: saveAsClick,
        },
        { type: "separator" },
        {
          label: "Close Tab",
          accelerator: "CmdOrCtrl+W",
          click: closeTabClick,
        },
        {
          label: "Close Window",
          accelerator: "Shift+CmdOrCtrl+W",
          click: closeActiveWindow,
        },
      ],
    },
    // { role: 'editMenu' }
    {
      label: "Edit",
      submenu: [
        { role: "undo" },
        { role: "redo" },
        { type: "separator" },
        { role: "cut" },
        { role: "copy" },
        { role: "paste" },
        ...(isMac
          ? [
              { role: "pasteAndMatchStyle" },
              { role: "delete" },
              { role: "selectAll" },
              { type: "separator" },
              {
                label: "Speech",
                submenu: [{ role: "startspeaking" }, { role: "stopspeaking" }],
              },
            ]
          : [{ role: "delete" }, { type: "separator" }, { role: "selectAll" }]),
      ],
    },
    // { role: 'viewMenu' }
    {
      label: "View",
      submenu: [
        { role: "reload" },
        { role: "forcereload" },
        { role: "toggledevtools" },
        { type: "separator" },
        { role: "resetzoom" },
        { role: "zoomin" },
        { role: "zoomout" },
        { type: "separator" },
        { role: "togglefullscreen" },
      ],
    },
    // { role: 'windowMenu' }
    {
      label: "Window",
      submenu: [
        { role: "minimize" },
        { role: "zoom" },
        ...(isMac
          ? [
              { type: "separator" },
              { role: "front" },
              { type: "separator" },
              { role: "window" },
            ]
          : [{ role: "close" }]),
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// todo: freeze menu items / initialize dummy handler on first start so the checks aren't needed

function newClick() {
  if (!windows.size) {
    createWindow();
  } else {
    out(menuKey, MENU_NEW);
  }
}

function openClick() {
  out(menuKey, MENU_OPEN);
}

function saveClick() {
  out(menuKey, MENU_SAVE);
}

function saveAsClick() {
  out(menuKey, MENU_SAVE_AS);
}

function closeTabClick() {
  out(menuKey, MENU_CLOSE_TAB);
}
