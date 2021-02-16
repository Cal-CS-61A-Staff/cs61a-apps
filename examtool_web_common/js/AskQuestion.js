import React, { useState } from "react";
import { Row, Card, Col, Form } from "react-bootstrap";
import { useExamData } from "./AlertsContext";
import FailText from "./FailText";
import LoadingButton from "./LoadingButton";

export default function AskQuestion({ send }) {
  const examData = useExamData();

  const [message, setMessage] = useState("");
  const [question, setQuestion] = useState("Overall Exam");
  const [isLoading, setIsLoading] = useState(false);
  const [failText, setFailText] = useState("");

  const submit = async () => {
    setIsLoading(true);
    const err = await send("ask_question", {
      question: question === "Overall Exam" ? null : question,
      message,
    });
    if (err) {
      setFailText(err);
    } else {
      setMessage("");
    }
    setIsLoading(false);
  };

  return (
    <Row>
      <Col>
        <Card>
          <Card.Header>Request Clarification</Card.Header>
          <Card.Body>
            <Form>
              <Form.Group>
                <Form.Control
                  as="textarea"
                  rows={3}
                  value={message}
                  placeholder="Send a private message to staff."
                  onChange={(e) => setMessage(e.target.value)}
                />
              </Form.Group>
              <Form.Group>
                <Form.Control
                  as="select"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  custom
                >
                  <option value={null}>Overall Exam</option>
                  {examData.questions.map((questionName) => (
                    <option key={questionName}>{questionName}</option>
                  ))}
                </Form.Control>
              </Form.Group>
              <Form.Group>
                <LoadingButton
                  loading={isLoading}
                  disabled={isLoading}
                  onClick={submit}
                >
                  Send
                </LoadingButton>
                <FailText text={failText} suffixType="alerts" />
              </Form.Group>
            </Form>
          </Card.Body>
        </Card>
        <br />
      </Col>
    </Row>
  );
}
