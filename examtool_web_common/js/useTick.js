import { useState } from "react";
import useInterval from "./useInterval";

export default function useTick() {
  const [time, setTime] = useState(Math.round(new Date().getTime() / 1000));
  useInterval(() => setTime(Math.round(new Date().getTime() / 1000)));
  return time;
}
