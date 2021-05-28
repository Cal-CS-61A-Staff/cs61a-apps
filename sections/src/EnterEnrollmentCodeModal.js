// @flow strict

import * as React from "react";
import Button from "react-bootstrap/Button";
import Modal from "react-bootstrap/Modal";
import FormControl from "react-bootstrap/FormControl";
import { useState } from "react";

type Props = {
  show: Boolean,
  onClose: () => void,
};

export default function AddEnrollmentCodeModal({ show, onClose }: Props) {
  const [enrollmentCode, setEnrollmentCode] = useState("");

  return (
    <Modal show={show} onHide={() => onClose(enrollmentCode)}>
      <Modal.Header closeButton>
        <Modal.Title>Enter Enrollment Code</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <FormControl
          value={enrollmentCode ?? ""}
          onChange={(e) => setEnrollmentCode(e.target.value)}
        />
      </Modal.Body>
      <Modal.Footer>
        <Button variant="success" onClick={() => onClose(enrollmentCode)}>
          Submit
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
