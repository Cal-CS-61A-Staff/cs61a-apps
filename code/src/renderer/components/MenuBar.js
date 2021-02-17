import React from "react";
import {
  MENU_NEW,
  MENU_OPEN,
  MENU_NEW_CONSOLE,
  MENU_SAVE,
  MENU_SAVE_AS,
  MENU_SETTINGS,
  MENU_SHARE,
  MENU_HELP,
  MENU_LOGIN,
  MENU_LOGOUT,
} from "../../common/communicationEnums.js";
import MenuElem from "./MenuElem.js";
import { useAuthData } from "../utils/okUtils.js";

export default function MenuBar() {
  const authData = useAuthData();

  const menuOptions = [
    { code: MENU_NEW, name: "New", shortcut: "mod+n" },
    { code: MENU_OPEN, name: "Open", shortcut: "mod+o" },
    { code: MENU_NEW_CONSOLE, name: "Console", shortcut: "mod+shift+c" },
    { code: MENU_SAVE, name: "Save", shortcut: "mod+s" },
    { code: MENU_SAVE_AS, name: "Save As", shortcut: "mod+shift+s" },
    { code: MENU_SHARE, name: "Share", shortcut: "mod+shift+option+s" },
    { code: MENU_SETTINGS, name: "Settings", shortcut: "mod+," },
    { code: MENU_HELP, name: "Help", shortcut: "f1" },
  ];

  if (authData.loggedOut) {
    menuOptions.push({
      code: MENU_LOGIN,
      name: "Login",
      shortcut: "mod+shift+l",
    });
  } else {
    menuOptions.push({
      code: MENU_LOGOUT,
      name: "Logout",
      shortcut: "mod+shift+l",
    });
  }

  const menuElems = menuOptions.map(
    // eslint-disable-next-line react/no-array-index-key
    (elem, index) => <MenuElem key={index} {...elem} />
  );
  return <div className="menuBar">{menuElems}</div>;
}
