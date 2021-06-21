// @flow strict

import * as React from "react";
import Button from "react-bootstrap/Button";
import Modal from "react-bootstrap/Modal";
import FormControl from "react-bootstrap/FormControl";
import { useState } from "react";

import type { SheetURL } from "./models";

type Props = {
  show: Boolean,
  onClose: (code: SheetURL) => void,
};

export default function ImportSectionsModal({ show, onClose }: Props) {
  const [sheet, setSheet] = useState("");

  return (
    <Modal show={show} onHide={() => onClose(sheet)}>
      <Modal.Header closeButton>
        <Modal.Title>Enter Spreadsheet URL</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <FormControl
          value={sheet ?? ""}
          onChange={(e) => setSheet(e.target.value)}
        />
      </Modal.Body>
      <Modal.Footer>
        <Button variant="success" onClick={() => onClose(sheet)}>
          Import
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
