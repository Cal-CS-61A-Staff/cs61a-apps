import { useRef } from "react";

let id = 0;

export default function useId() {
  return useRef(++id);
}
