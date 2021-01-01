import * as React from "react";
import CommandIcon from "./CommandIcon.js";

export default function NavButton(props) {
  if (props.prev) {
    return (
      <CommandIcon
        commandName="Prev"
        style={{ backgroundColor: "black" }}
        onClick={props.onClick}
      />
    );
  } else {
    return (
      <CommandIcon
        commandName="Next"
        style={{ backgroundColor: "black" }}
        onClick={props.onClick}
      />
    );
  }
}
