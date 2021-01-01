import React, { useEffect, useState } from "react";
import { Button, Card, Form, Modal, ListGroup } from "react-bootstrap";
import { useTime } from "./AlertsContext";
import { getToken } from "./auth";
import { Group, postRenderFormat } from "./Exam";
import Question from "./Question";
import StaffMessageReplyBox from "./StaffMessageReplyBox";
import { timeDeltaMinutesString } from "./timeUtils";
import post from "./post";

export default function StaffMessagesList({
  selectedExam,
  staffData,
  onUpdate,
}) {
  const time = useTime();

  const [showModal, setShowModal] = useState(false);
  const [questionData, setQuestionData] = useState(null);
  const [compactMode, setCompactMode] = useState(false);

  const loadQuestion = async (id, student) => {
    setQuestionData(null);
    setShowModal(true);
    try {
      const resp = await post("get_question", {
        token: getToken(),
        exam: selectedExam,
        student,
        id,
      });
      const data = await resp.json();
      if (!data.success) {
        throw Error();
      }
      setQuestionData(data.question);
    } catch {
      setShowModal(false);
    }
  };

  useEffect(postRenderFormat, [questionData]);

  const makeReplyBox = (id, compact) => (
    <StaffMessageReplyBox
      message={id}
      compact={compact}
      exam={selectedExam}
      onUpdate={onUpdate}
    />
  );

  return (
    <>
      <h3>Private Messages</h3>
      <Form.Group>
        <Form.Check
          id="staffCheckbox"
          custom
          type="checkbox"
          label="Compact Mode"
          value={compactMode}
          onChange={(e) => setCompactMode(e.target.checked)}
        />
      </Form.Group>
      {staffData.messages.map(
        ({
          id,
          responses,
          email,
          message,
          question,
          timestamp: messageTime,
        }) => (
          <div key={id}>
            <Card
              bg={responses.length === 0 ? "danger" : "default"}
              text={responses.length === 0 ? "white" : "dark"}
            >
              <Card.Header>
                <b>
                  {responses.length === 0
                    ? "Unresolved Thread"
                    : "Resolved Thread"}
                </b>{" "}
                [{question || "Overall Exam"}]{" "}
                {responses.length === 0 && (
                  <span style={{ float: "right", marginLeft: 10 }}>
                    {" "}
                    {makeReplyBox(id, true)}{" "}
                  </span>
                )}
                {question != null && (
                  <Button
                    style={{ float: "right" }}
                    variant="primary"
                    size="sm"
                    onClick={() => loadQuestion(question, email)}
                  >
                    View Question
                  </Button>
                )}
              </Card.Header>
              <ListGroup variant="flush">
                <ListGroup.Item
                  style={{ whiteSpace: "pre-wrap" }}
                  variant="secondary"
                >
                  <b>{email}: </b>
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
                      {response} ({timeDeltaMinutesString(time - responseTime)})
                    </ListGroup.Item>
                  )
                )}
                {!compactMode && (
                  <ListGroup.Item style={{ whiteSpace: "pre-wrap" }}>
                    {makeReplyBox(id, false)}
                  </ListGroup.Item>
                )}
              </ListGroup>
            </Card>
            <br />
          </div>
        )
      )}
      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>Question Preview</Modal.Header>
        <Modal.Body>
          {questionData != null &&
            (questionData.type === "group" ? (
              <Group
                group={questionData}
                number={questionData.index.slice(0, -1)}
              />
            ) : (
              <Question
                question={questionData}
                number={questionData.index.slice(0, -1)}
              />
            ))}
        </Modal.Body>
        <Modal.Footer>
          <Button onClick={() => setShowModal(false)}>Close</Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}
