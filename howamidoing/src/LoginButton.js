import React from "react";
import logo from "./ok-logo.svg";

export default function LoginButton({ onClick }) {
    return (
        <div className="alert alert-danger" role="alert">
            You are not logged in with an account that is registered for this class.
            Try logging in with a valid okpy account.
            <button
                className="mt-3 btn btn-lg btn-warning btn-block"
                type="button"
                onClick={onClick}
            >
Log in with
                {" "}
                <img
                    src={logo}
                    alt="Log in with OK"
                    style={{ height: "1.5em", width: "1.5em" }}
                />
            </button>
        </div>
    );
}
