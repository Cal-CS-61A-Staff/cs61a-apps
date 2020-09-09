// @flow strict

import { useContext, useEffect, useState } from "react";
import * as React from "react";
import Button from "react-bootstrap/Button";
import FormControl from "react-bootstrap/FormControl";
import Modal from "react-bootstrap/Modal";
import SectionStateContext from "./SectionStateContext";
import useSectionAPI from "./useSectionAPI";

type Props = {
  show: boolean,
  onClose: () => void,
};

export default function AddStudentModal({ show, onClose }: Props) {
  const [email, setEmail] = useState("");

  useEffect(() => {
    if (!show) {
      setEmail("");
    }
  }, [show]);

  const section = useContext(SectionStateContext);
  const addStudent = useSectionAPI("add_student");

  return (
    <Modal show={show} onHide={onClose}>
      <Modal.Header closeButton>
        <Modal.Title>Add Student</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <FormControl
          placeholder="Student Email Address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
        <Button
          variant="primary"
          onClick={() =>
            addStudent({ section_id: section.id, email }).finally(onClose)
          }
        >
          Add Student
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
