import { useEffect } from "react";

import { send } from "./communication";
import { CLAIM_MENU } from "../../common/communicationEnums.js";

let remote;
if (ELECTRON) {
  // eslint-disable-next-line global-require
  ({ remote } = require("electron"));
}

export default function claimMenu(handlers) {
  let detach;

  claim();

  function claim() {
    [, , detach] = send({ type: CLAIM_MENU }, (option) => {
      if (!handlers[option]) {
        console.error(option, "not available right now!");
        return;
      }
      handlers[option]();
    });
  }

  if (ELECTRON) {
    remote.getCurrentWindow().on("focus", () => {
      detach();
      claim();
    });
  }

  return () => {
    detach();
  };
}

export function useMenu(handlers) {
  useEffect(claimMenu(handlers), []);
}
