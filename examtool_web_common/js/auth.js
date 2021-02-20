import { auth2 } from "gapi";

export function getToken() {
  return window.location.hostname === "localhost"
    ? null
    : auth2.getAuthInstance().currentUser.get().getAuthResponse(true).id_token;
}

export function getAuthParams() {
  return {
    token: getToken(),
    ...getLoginAsParams(),
  };
}

export function getLoginAsParams() {
  const hash = window.location.hash.slice(1);
  return hash
    ? Object.fromEntries(hash.split(";").map((part) => part.split("=")))
    : {};
}

export function inAdminMode() {
  return !!getLoginAsParams().loginas;
}
