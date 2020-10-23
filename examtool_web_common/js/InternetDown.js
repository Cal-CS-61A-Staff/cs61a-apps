import React from "react";
import { Modal } from "react-bootstrap";
import Button from "react-bootstrap/Button";

export default function InternetDown({ onHide }) {
  return (
    <Modal show>
      <Modal.Header closeButton>
        <Modal.Title>Network Connection Lost!</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        The tool was unable to save due to a network error. Please try saving
        again. If this error persists, refresh the page and try again, or submit
        your answers by email. Note that if the exam has ended, you should not
        refresh, but instead just send us your answers by email directly.
      </Modal.Body>
      <Modal.Footer>
        <Button variant="danger" onClick={onHide}>
          I know connection is lost. I am still going back to the exam
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
