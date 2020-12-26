// eslint-disable-next-line import/no-extraneous-dependencies
import { app, BrowserWindow } from "electron";
import * as path from "path";
import { format as formatUrl } from "url";
import { initializeMenu } from "./initializeMenu.js";
import { addHandlers } from "./communication.js";
import { startOkServer } from "./ok_interface.js";

const isDevelopment = process.env.NODE_ENV !== "production";

// global reference to mainWindow (necessary to prevent window from being garbage collected)
export const windows = new Set();
let activeWindow;

let initialPath = "";

let ready = false;

// eslint-disable-next-line import/prefer-default-export
export function createWindow() {
  const window = new BrowserWindow({
    show: false,
    webPreferences: {
      webSecurity: !isDevelopment,
    },
  });

  window.once("ready-to-show", () => {
    window.show();
  });

  if (isDevelopment) {
    window.webContents.openDevTools();
  }

  if (isDevelopment) {
    window.loadURL(`http://localhost:${process.env.ELECTRON_WEBPACK_WDS_PORT}`);
  } else {
    window.loadURL(
      formatUrl({
        pathname: path.join(__dirname, "index.html"),
        protocol: "file",
        slashes: true,
        query: { initialPath },
      })
    );
  }

  initialPath = null;

  window.on("focus", () => {
    activeWindow = window;
  });

  window.on("closed", () => {
    if (window === activeWindow) {
      activeWindow = null;
    }
    windows.delete(window);
  });

  window.webContents.on("devtools-opened", () => {
    window.focus();
    setImmediate(() => {
      window.focus();
    });
  });

  windows.add(window);
}

export function closeActiveWindow() {
  if (activeWindow) {
    activeWindow.close();
  }
}

// quit application when all windows are closed
app.on("window-all-closed", () => {
  // on macOS it is common for applications to stay open until the user explicitly quits
  if (process.platform !== "darwin") {
    setTimeout(() => app.quit(), 0);
  }
});

app.on("activate", () => {
  // on macOS it is common to re-create a window even after all windows have been closed
  if (windows.size === 0) {
    createWindow();
  }
});

// TODO: implement equivalent for Windows!
app.on("open-file", (event, initPath) => {
  event.preventDefault();
  initialPath = initPath;
  if (ready) {
    createWindow();
  }
});

// create main BrowserWindow when electron is ready
app.on("ready", () => {
  createWindow();
  ready = true;
});

initializeMenu();
addHandlers();
startOkServer();
