// @flow strict

import { useCallback, useContext } from "react";
import type { SectionDetails } from "./models";
import SectionStateContext from "./SectionStateContext";
import useAPI from "./useAPI";

type Callback = (SectionDetails) => void;

export default function useStateAPI(method: string, callback: ?Callback) {
  const { updateState } = useContext(SectionStateContext);

  const wrappedCallback = useCallback(
    (state) => {
      updateState(state);
      if (callback) {
        callback(state);
      }
    },
    [updateState, callback]
  );

  return useAPI(method, wrappedCallback);
}
