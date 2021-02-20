import React, { useEffect, useState } from "react";
import { auth2, signin2, load } from "gapi";
import { getLoginAsParams } from "./auth";

export default function GoogleSignInButton({ onSuccess }) {
  const [username, setUsername] = useState(
    window.location.hostname === "localhost" ? "exam-test@berkeley.edu" : ""
  );

  const logout = (e) => {
    e.preventDefault();
    setUsername("");
    auth2.getAuthInstance().signOut();
    window.location.reload();
  };

  useEffect(() => {
    if (username) {
      onSuccess(username);
      return;
    }
    load("auth2", () => {
      signin2.render("signInButton", {
        width: 200,
        longtitle: true,
        onsuccess: (user) => {
          setUsername(user.getBasicProfile().getEmail());
          onSuccess(user.getBasicProfile().getEmail());
        },
      });
    });
  }, []);

  if (username) {
    return (
      <>
        You have signed in as <b>{getLoginAsParams().loginas || username}</b>.{" "}
        {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
        <a href="#" onClick={logout}>
          Log out
        </a>{" "}
        if this is not the right account.
      </>
    );
  }

  return (
    <>
      First, sign into Google using your CalNet account.
      <div
        id="signInButton"
        className="g-signin2"
        data-onsuccess="onSignIn"
        data-theme="dark"
      />
    </>
  );
}
