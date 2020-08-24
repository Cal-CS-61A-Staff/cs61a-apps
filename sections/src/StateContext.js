// @flow strict

import * as React from "react";

import type { State } from "./models";

export default React.createContext<{
  ...State,
  updateState: (State) => void,
}>({
  currentUser: null,
  sections: [],
  taughtSections: [],
  enrolledSection: null,
  updateState: () => {},
});
