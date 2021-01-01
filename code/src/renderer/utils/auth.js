import post from "../../common/post.js";

export function login() {
  window.open("/oauth/popup_login", "_blank");
}

export function logout() {
  window.open("/oauth/popup_logout", "_blank");
}

const handlers = new Set();
let currAuthData = { loggedOut: true };

export async function checkLoggedIn() {
  let newAuthData;
  try {
    newAuthData = await post("/api/user");
  } catch {
    newAuthData = { loggedOut: true };
  }
  if (JSON.stringify(newAuthData) !== JSON.stringify(currAuthData)) {
    currAuthData = newAuthData;
    for (const { handler } of handlers) {
      handler(currAuthData);
    }
  }
}

export function getCurrAuthData() {
  return currAuthData;
}

checkLoggedIn();

window.addEventListener("focus", checkLoggedIn);

export function addAuthListener(handler) {
  const wrappedHandler = { handler };
  handlers.add(wrappedHandler);
  return () => {
    handlers.delete(wrappedHandler);
  };
}
