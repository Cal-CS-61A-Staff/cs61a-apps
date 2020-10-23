import { auth2 } from "gapi";

// eslint-disable-next-line import/prefer-default-export
export function getToken() {
  return window.location.hostname === "localhost"
    ? null
    : auth2.getAuthInstance().currentUser.get().getAuthResponse(true).id_token;
}
