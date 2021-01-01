import { useEffect, useState } from "react";

// eslint-disable-next-line import/prefer-default-export
export function useAsync(callback, initialState = null, deps = []) {
  const [data, setData] = useState(initialState);

  useEffect(() => {
    let go = true;
    setData(initialState);
    Promise.resolve(callback()).then((x) => {
      if (go) setData(x);
    });
    return () => {
      go = false;
    };
  }, deps);

  return data;
}
