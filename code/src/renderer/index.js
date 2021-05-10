/* eslint-disable global-require */
import * as React from "react";
import * as ReactDOM from "react-dom";

import path from "path";

import "./style.global.css";
import { PYTHON } from "../common/languages";
import { COMPILE_PY_FILE } from "../languages/python/constants/communicationEnums";
import App from "./components/App.js";
import { send } from "./utils/communication";

if (ELECTRON) {
  const amdLoader = require("monaco-editor/min/vs/loader.js");
  const amdRequire = amdLoader.require;
  amdRequire.config({
    baseUrl: uriFromPath(path.join(__static, "/monaco-editor/min")),
  });
  // workaround monaco-css not understanding the environment
  // eslint-disable-next-line no-restricted-globals
  self.module = undefined;
  amdRequire(["vs/editor/editor.main"], init);
} else {
  init();
}

function uriFromPath(_path) {
  let pathName = path.resolve(_path).replace(/\\/g, "/");
  if (pathName.length > 0 && pathName.charAt(0) !== "/") {
    pathName = `/${pathName}`;
  }
  return encodeURI(`file://${pathName}`);
}

function injectScript(src) {
  return new Promise((resolve) => {
    const script = document.createElement("script");
    if (ELECTRON) {
      script.src = uriFromPath(path.join(__static, src));
    } else {
      script.src = path.join(__static, src);
    }
    script.async = false;
    document.body.appendChild(script);
    script.onload = () => resolve();
  });
}

function injectDiv(id) {
  const elem = document.createElement("div");
  elem.id = id;
  document.body.appendChild(elem);
}

function render(Component) {
  const rawUrl = document.location.toString();
  const parsedUrl = new URL(rawUrl);
  const initialPath = parsedUrl.searchParams.get("initialPath");
  ReactDOM.render(
    <Component path={initialPath} />,
    document.getElementById("app")
  );
}

async function init() {
  Pace.options.ajax.trackWebSockets = false;

  await Promise.all([
    injectScript("d3.v2.min.js"),
    injectScript("jquery-1.8.2.min.js"),
    injectScript("jquery.ba-bbq.min.js"),
    injectScript("jquery-ui.min.js"),
    injectScript("jquery.jsPlumb-1.3.10-all-min.js"),
    injectScript("python/pytutor.js"),
  ]);

  if (!ELECTRON) {
    injectDiv("app");
    injectDiv("modalOverlay");
  }

  if (!SCHEME_COMPILE) {
    render(App);
  }
}

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("service-worker.js");
    console.log("service worker registered!");
  });
}

if (SCHEME_COMPILE) {
  const interpreter =
    require("./../languages/scheme/web/IGNORE_needed.py").default;
  send(
    { type: COMPILE_PY_FILE, code: interpreter, handler: PYTHON },
    (output) => {
      document.head.innerHTML = "";
      document.body.innerText = output;
    }
  );
}
