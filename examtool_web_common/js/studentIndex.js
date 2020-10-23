import React from "react";
import { render } from "react-dom";
import StudentApp from "./StudentApp";

function init() {
  render(<StudentApp />, document.querySelector("#root"));
}

init();
