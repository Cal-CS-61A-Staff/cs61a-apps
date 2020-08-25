// @flow strict

import * as React from "react";

type MessageContextType = {
  pushMessage: (string) => void,
};

export default React.createContext<MessageContextType>({
  pushMessage: () => {},
});
