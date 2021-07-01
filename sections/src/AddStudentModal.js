// @flow strict

import { useEffect, useState } from "react";
import * as React from "react";
import Button from "react-bootstrap/Button";
import FormControl from "react-bootstrap/FormControl";
import Modal from "react-bootstrap/Modal";

type Props = {
  show: boolean,
  onAdd: (string) => Promise<void>,
  onClose: () => void,
};

export default function AddStudentModal({ show, onAdd, onClose }: Props) {
  const [email, setEmail] = useState("");

  useEffect(() => {
    if (!show) {
      setEmail("");
    }
  }, [show]);

  return (
    <Modal show={show} onHide={onClose}>
      <Modal.Header closeButton>
        <Modal.Title>Add Student(s)</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <FormControl
          placeholder="Student(s) Email Address (comma-separated)"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
        <Button variant="primary" onClick={() => onAdd(email).then(onClose)}>
          Add Student(s)
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
