import * as React from "react";
import CommandIcon from "./CommandIcon";

export default function RunStopButton(props) {
  if (props.codeRunning) {
    return <CommandIcon commandName="Stop" onClick={props.onStop} />;
  } else {
    return <CommandIcon commandName="Restart" onClick={props.onRestart} />;
  }
}
