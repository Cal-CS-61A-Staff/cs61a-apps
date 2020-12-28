import React from "react";
import PathIndicator from "./PathIndicator";
import NavBarIcons from "./NavBarIcons";

export default function NavBar(props) {
  return (
    <span className="navBar">
      {ELECTRON ? <PathIndicator path={props.path} /> : false}
      <NavBarIcons onActionClick={props.onActionClick} />
    </span>
  );
}
