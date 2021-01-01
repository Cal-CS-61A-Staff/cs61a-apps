import { exit, out } from "./webBackend.js";

let menuKey = null;

export function assignMenuKey(key) {
  if (menuKey) {
    exit(menuKey);
  }
  menuKey = key;
}

export function sendMenuEvent(code) {
  out(menuKey, code);
}
