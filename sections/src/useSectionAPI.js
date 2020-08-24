// @flow strict

import { useCallback, useContext } from "react";
import type { SectionDetails } from "models";
import post from "./common/post";
import SectionStateContext from "./SectionStateContext";

export default function useSectionAPI(
  method: string,
  callback: ?(SectionDetails) => void
) {
  const { updateState } = useContext(SectionStateContext);

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
