// @flow strict

import { useCallback, useContext } from "react";
import type { State } from "models.js";
import post from "./common/post";
import StateContext from "./StateContext";

export default function useAPI(method: string, callback: ?(State) => mixed) {
  const { updateState } = useContext(StateContext);

  return useCallback(
    async (args: { [key: string]: any } = {}) => {
      const resp = await post(`/api/${method}`, args);
      if (resp.success) {
        updateState(resp.data);
        if (callback) {
          callback(resp.data);
        }
      } else {
        // TODO: display exception
      }
    },
    [method, callback, updateState]
  );
}
