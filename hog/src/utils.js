// @flow
import { useEffect, useState, useRef } from "react";

export function useAsync<T>(
  callback: () => T,
  initialState: ?T = null,
  deps: Array<mixed> = []
) {
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

export function useInterval(callback: () => mixed, interval: number) {
  const savedCallback = useRef(callback);

  savedCallback.current = callback;

  // eslint-disable-next-line consistent-return
  useEffect(() => {
    if (interval !== null) {
      const timer = setInterval(() => savedCallback.current(), interval);
      return () => clearInterval(timer);
    }
  }, [interval]);
}

export function wait(delay: number): Promise<mixed> {
  return new Promise((resolve) => setTimeout(resolve, delay));
}
