import React from "react";
import { render } from "react-dom";
import AdminApp from "./examtool_web_common/js/AdminApp";

function init() {
  render(<AdminApp />, document.querySelector("#root"));
}

init();
