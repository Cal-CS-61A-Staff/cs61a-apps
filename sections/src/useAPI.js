// @flow strict

import { useCallback, useContext } from "react";
import type { State } from "models.js";
import post from "./common/post";
import MessageContext from "./MessageContext";
import StateContext from "./StateContext";

export default function useAPI(
  method: string,
  callback: ?({ ...State, custom: { [string]: ?string } }) => mixed
) {
  const { updateState } = useContext(StateContext);
  const { pushMessage } = useContext(MessageContext);

  return useCallback(
    async (args: { [key: string]: any } = {}) => {
      try {
        const resp = await post(`/api/${method}`, args, true);
        if (resp.success) {
          updateState(resp.data);
          if (callback) {
            callback(resp.data);
          }
        } else {
          pushMessage(resp.message ?? "Unknown error.");
        }
      } catch (e) {
        console.error(e);
        pushMessage("Something went wrong.");
      }
    },
    [method, callback, pushMessage, updateState]
  );
}
