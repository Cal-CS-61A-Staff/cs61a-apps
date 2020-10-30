import React from "react";
import { render } from "react-dom";
import StudentApp from "./examtool_web_common/js/StudentApp";

function init() {
  render(<StudentApp />, document.querySelector("#root"));
}

init();
