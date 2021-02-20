import { auth2 } from "gapi";

export function getToken() {
  return window.location.hostname === "localhost"
    ? null
    : auth2.getAuthInstance().currentUser.get().getAuthResponse(true).id_token;
}

export function getAuthParams() {
  const hash = window.location.hash.slice(1);
  const parts = hash
    ? Object.fromEntries(hash.split(";").map((part) => part.split("=")))
    : {};

  return {
    token: getToken(),
    ...parts,
  };
}

export function inAdminMode() {
  return !!getAuthParams().loginas;
}
