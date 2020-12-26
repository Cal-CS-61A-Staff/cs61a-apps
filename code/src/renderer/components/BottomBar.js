import * as React from "react";
import { MENU_NEW } from "../../common/communicationEnums.js";
import MenuElem from "./MenuElem.js";

export default function MenuBar() {
  const menuOptions = [
    { code: MENU_NEW, name: "New Terminal", shortcut: "mod+alt+t" },
  ];
  const menuElems = menuOptions.map(
    // eslint-disable-next-line react/no-array-index-key
    (elem, index) => <MenuElem key={index} flexBasis={130} {...elem} />
  );
  return <div className="bottomBar">{menuElems}</div>;
}
