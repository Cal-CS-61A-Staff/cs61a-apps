import React from "react";
import { render } from "react-dom";
import AdminApp from "./AdminApp";

function init() {
  render(<AdminApp />, document.querySelector("#root"));
}

init();
