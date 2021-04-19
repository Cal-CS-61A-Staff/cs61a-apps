import { useEffect, useRef, useState } from "react";

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

export function useRequestAnimationFrame(callback) {
  let initialTime = null;
  let running = true;

  const callbackRef = useRef();
  callbackRef.current = callback;

  useEffect(() => {
    const worker = (time) => {
      if (running) {
        if (!initialTime) {
          initialTime = time;
        }
        const delta = time - initialTime;
        callbackRef.current(delta);
        requestAnimationFrame(worker);
      } else {
        initialTime = null;
      }
    };
    requestAnimationFrame(worker);
    return () => {
      running = false;
    };
  }, []);
}
