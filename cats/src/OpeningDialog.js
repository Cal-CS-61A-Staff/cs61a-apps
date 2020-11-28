import React from "react";
import Modal from "react-bootstrap/Modal";
import Button from "react-bootstrap/Button";
import "./OpeningDialog.css";
import { Mode } from "./App.js";

export default function OpeningDialog(props) {
  const setMode = (mode) => () => {
    props.setMode(mode);
  };

  return (
    <Modal
      size="sm"
      aria-labelledby="contained-modal-title-vcenter"
      centered
      show={props.show}
    >
      <Modal.Header>
        <Modal.Title>Welcome!</Modal.Title>
      </Modal.Header>

      <Modal.Body>
        <p>Welcome to the 61A Typing Test!</p>
        <p>Select a mode below to begin.</p>
      </Modal.Body>
      <Modal.Footer>
        <Button onClick={setMode(Mode.SINGLE)} variant="primary">
          Single Player
        </Button>
        <Button onClick={setMode(Mode.WAITING)} variant="warning">
          Multiplayer
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
