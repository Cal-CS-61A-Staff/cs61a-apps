import React from "react";
import { render } from "react-dom";
import StaffApp from "./examtool_web_common/js/StaffApp";

function init() {
  render(<StaffApp />, document.querySelector("#root"));
}

init();
