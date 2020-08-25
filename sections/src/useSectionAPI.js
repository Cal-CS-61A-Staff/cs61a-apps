// @flow strict

import { useCallback, useContext } from "react";
import type { SectionDetails } from "models";
import post from "./common/post";
import MessageContext from "./MessageContext";
import SectionStateContext from "./SectionStateContext";

export default function useSectionAPI(
  method: string,
  callback: ?(SectionDetails) => void
) {
  const { updateState } = useContext(SectionStateContext);
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
      } catch {
        pushMessage("Something went wrong.");
      }
    },
    [method, callback, updateState]
  );
}
