// @flow strict

import { useCallback, useContext } from "react";
import type { State } from "./models";
import StateContext from "./StateContext";
import useAPI from "./useAPI";

type Callback = ({ ...State, custom: { [string]: ?string } }) => mixed;

export default function useStateAPI(method: string, callback: ?Callback) {
  const { updateState } = useContext(StateContext);

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
