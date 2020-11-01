import React from "react";
import { Card, Row, Col, ListGroup } from "react-bootstrap";
import { useExamData, useTime } from "./AlertsContext";
import { timeDeltaMinutesString } from "./timeUtils";

export default function StudentMessagesList() {
  const time = useTime();
  const examData = useExamData();

  if (examData.messages.length === 0) {
    return null;
  }

  return (
    <Row>
      <Col>
        {examData.messages.map(
          ({ id, message, question, time: messageTime, responses }) => (
            <div key={id}>
              <Card>
                <Card.Header>
                  <b>
                    {responses.length === 0
                      ? "Unresolved Thread"
                      : "Resolved Thread"}
                  </b>{" "}
                  [{question}]
                </Card.Header>
                <ListGroup variant="flush">
                  <ListGroup.Item key={id} style={{ whiteSpace: "pre-wrap" }}>
                    <b>You: </b>
                    {message} ({timeDeltaMinutesString(time - messageTime)})
                  </ListGroup.Item>
                  {responses.map(
                    ({
                      id: replyID,
                      message: response,
                      timestamp: responseTime,
                    }) => (
                      <ListGroup.Item
                        key={replyID}
                        style={{ whiteSpace: "pre-wrap" }}
                      >
                        <b>Staff: </b>
                        {response} (
                        {timeDeltaMinutesString(time - responseTime)})
                      </ListGroup.Item>
                    )
                  )}
                </ListGroup>
              </Card>
              <br />
            </div>
          )
        )}
      </Col>
    </Row>
  );
}
