import React from "react";
import { render } from "react-dom";
import AlertsApp from "./AlertsApp";

function init() {
  render(<AlertsApp />, document.querySelector("#root"));
}

init();
