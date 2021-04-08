// @flow strict

import * as React from "react";
import Button from "react-bootstrap/Button";
import ListGroup from "react-bootstrap/ListGroup";
import Modal from "react-bootstrap/Modal";
import styled from "styled-components";
import { sessionStartTimes } from "./models";
import type { Section } from "./models";
import useSectionAPI from "./useSectionAPI";

type Props = {
  section: Section,
  show: boolean,
  onClose: () => void,
};

const FloatRightDiv = styled.div`
  float: right;
`;

export default function AddSessionModel({ section, show, onClose }: Props) {
  const startSession = useSectionAPI("start_session");
  const startTimes = sessionStartTimes(section);

  return (
    <Modal show={show} onHide={onClose}>
      <Modal.Header closeButton>
        <Modal.Title>Add Missing Session</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <ListGroup variant="flush">
          {startTimes.map((startTime) => (
            <ListGroup.Item>
              {startTime.format("MMMM D")}{" "}
              <FloatRightDiv>
                <Button
                  size="sm"
                  onClick={() =>
                    startSession({
                      section_id: section.id,
                      start_time: startTime.unix(),
                    }).finally(onClose)
                  }
                >
                  Add
                </Button>
              </FloatRightDiv>
            </ListGroup.Item>
          ))}
        </ListGroup>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
