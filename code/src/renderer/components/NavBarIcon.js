import React from "react";
import CommandIcon from "./CommandIcon";

export default function NavBarIcon(props) {
  const callback = () => props.onActionClick(props.commandName.toLowerCase());
  return (
    <>
      <span style={{ marginLeft: 5 }} />
      <CommandIcon commandName={props.commandName} onClick={callback} />
    </>
  );
}
