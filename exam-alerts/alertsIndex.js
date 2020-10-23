import React from "react";
import { render } from "react-dom";
import AlertsApp from "./examtool_web_common/js/AlertsApp";

function init() {
  render(<AlertsApp />, document.querySelector("#root"));
}

init();
