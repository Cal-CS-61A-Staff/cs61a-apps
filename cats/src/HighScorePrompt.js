import React, { useState, useRef } from "react";
import Cookies from "js-cookie";
import Modal from "react-bootstrap/Modal";
import CaptchaChallenge from "./CaptchaChallenge";
import CaptchaPrompt from "./CaptchaPrompt";
import NameForm from "./NameForm";
import post from "./post";

export default function HighScorePrompt({
  show,
  onHide,
  needVerify,
  wpm,
  onSubmit,
}) {
  const [images, setImages] = useState([]);
  const [lastWordLen, setLastWordLen] = useState([]);
  const [message, setMessage] = useState("");
  const [verified, setVerified] = useState(!needVerify);
  const token = useRef(null);

  if (!show && images.length) {
    setImages([]);
  }

  const requestChallenge = async () => {
    const {
      images: receivedImages,
      token: receivedToken,
      lastWordLen: receivedLastWordLen,
    } = await post("/request_wpm_challenge", {
      user: Cookies.get("user"),
    });
    setImages(receivedImages);
    setLastWordLen(receivedLastWordLen);
    token.current = receivedToken;
  };

  const submitChallenge = async (typed) => {
    const {
      success,
      message: failureMessage,
      token: successToken,
    } = await post("/claim_wpm_challenge", {
      user: Cookies.get("user"),
      token: token.current,
      typed,
      claimedWpm: wpm,
    });
    if (success) {
      setVerified(true);
      Cookies.set("token", successToken);
    } else {
      setMessage(`The server said: ${failureMessage} Please try again.`);
      setImages([]);
    }
  };

  const captcha = images.length ? (
    <CaptchaChallenge
      images={images}
      lastWordLen={lastWordLen}
      onSubmit={submitChallenge}
    />
  ) : (
    <CaptchaPrompt message={message} onClick={requestChallenge} />
  );
  const contents = verified ? <NameForm onSubmit={onSubmit} /> : captcha;

  return (
    <Modal
      size="md"
      aria-labelledby="contained-modal-title-vcenter"
      centered
      show={show}
      onHide={onHide}
    >
      <Modal.Header closeButton>
        <Modal.Title className="Header">High Score</Modal.Title>
      </Modal.Header>

      <Modal.Body>{contents}</Modal.Body>
    </Modal>
  );
}
