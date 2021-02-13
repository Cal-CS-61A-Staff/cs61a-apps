import { useEffect, useState } from "react";
import { CLAIM_SETTINGS } from "../../common/communicationEnums";

import { send } from "./communication";

export default function useSettings() {
  const [settings, setSettings] = useState({});

  useEffect(() => {
    const [, , detach] = send({ type: CLAIM_SETTINGS }, (raw) =>
      setSettings(JSON.parse(raw))
    );

    return detach;
  }, []);

  return settings;
}
