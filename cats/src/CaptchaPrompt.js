import React from "react";

export default function CaptchaPrompt({ message, onClick }) {
  const defaultMessage =
    "However, you first need to complete this Captcha challenge to" +
    " validate your WPM. Click the button to receive your challenge.";
  const displayedMessage = message || defaultMessage;
  return (
    <>
      <p>
        Congratulations! Your WPM is fast enough to place on our leaderboard!
      </p>
      <p>{displayedMessage}</p>
      <div className="form-group" onClick={onClick}>
        <button type="button" className="btn btn-primary">
          Request Challenge
        </button>
      </div>
      <small id="emailHelp" className="form-text text-muted">
        You'll need to type at a speed similar to your current WPM to pass the
        check. It's OK if you make mistakes or type a bit slower. After you pass
        the challenge, you won't be asked again for some time.
      </small>
    </>
  );
}
