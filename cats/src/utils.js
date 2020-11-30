import { useEffect, useRef } from "react";

export const getCurrTime = () => new Date().getTime() / 1000;

export const formatNum = (num) => (num ? num.toFixed(1) : "None");

export function useInterval(callback, delay) {
  const savedCallback = useRef();

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  // eslint-disable-next-line consistent-return
  useEffect(() => {
    function tick() {
      savedCallback.current();
    }
    if (delay !== null) {
      const id = setInterval(tick, delay);
      return () => clearInterval(id);
    }
  }, [delay]);
}

// https://stackoverflow.com/questions/1349404/generate-random-string-characters-in-javascript
export function randomString(len) {
  const charSet =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let out = "";
  for (let i = 0; i < len; i++) {
    const randomPoz = Math.floor(Math.random() * charSet.length);
    out += charSet.substring(randomPoz, randomPoz + 1);
  }
  return out;
}
