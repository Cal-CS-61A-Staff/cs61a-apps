import React from "react";
import { Badge, Card, Row, Col, ListGroup } from "react-bootstrap";
import { useExamData, useTime, useStale } from "./AlertsContext";
import { timeDeltaMinutesString } from "./timeUtils";

export default function StudentAlertsList() {
  const time = useTime();
  const examData = useExamData();
  const stale = useStale();

  return (
    <Row>
      <Col>
        <Card>
          <Card.Header>
            Announcements
            {stale && (
              <Badge style={{ float: "right" }} variant="danger">
                Disconnected
              </Badge>
            )}
          </Card.Header>
          <ListGroup variant="flush">
            {examData.announcements.map(
              ({ id, message, question, timestamp, private: isPrivate }) => (
                <ListGroup.Item key={id} style={{ whiteSpace: "pre-wrap" }}>
                  <b>[{isPrivate ? "Private" : question}]</b> {message} (
                  {timeDeltaMinutesString(time - timestamp)})
                </ListGroup.Item>
              )
            )}
          </ListGroup>
        </Card>
      </Col>
    </Row>
  );
}
