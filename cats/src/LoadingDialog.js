import React from "react";
import Modal from "react-bootstrap/Modal";
import Spinner from "react-bootstrap/Spinner";
import "./LoadingDialog.css";

export default function LoadingDialog(props) {
  return (
    <Modal
      size="lg"
      aria-labelledby="contained-modal-title-vcenter"
      centered
      show={props.show}
    >
      <Modal.Body>
        <div className="Spinner">
          <p>Looking for opponents...</p>
          <p>{props.numPlayers - 1} other player(s) found so far!</p>
          <Spinner animation="border" />
        </div>
      </Modal.Body>
    </Modal>
  );
}
