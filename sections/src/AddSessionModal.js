// @flow strict

import moment from "moment";
import { useMemo } from "react";
import * as React from "react";
import Button from "react-bootstrap/Button";
import ListGroup from "react-bootstrap/ListGroup";
import Modal from "react-bootstrap/Modal";
import styled from "styled-components";
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

  const sessionStartTimes = useMemo(() => {
    let time = moment.unix(section.startTime);
    const out = [];
    while (time.isBefore(moment().subtract(3, "days"))) {
      out.push(time);
      time = time.clone().add(7, "days");
    }
    return out;
  }, [section]);

  return (
    <Modal show={show} onHide={onClose}>
      <Modal.Header closeButton>
        <Modal.Title>Add Missing Session</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <ListGroup variant="flush">
          {sessionStartTimes.map((startTime) => (
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
