import React, { useState } from "react";
import { Row, Card, Col, Form } from "react-bootstrap";
import { useExamData } from "./AlertsContext";
import FailText from "./FailText";
import LoadingButton from "./LoadingButton";
import post from "./post";

export default function AskQuestion({ exam, onUpdate }) {
  const examData = useExamData();

  const [message, setMessage] = useState("");
  const [question, setQuestion] = useState("Overall Exam");
  const [isLoading, setIsLoading] = useState(false);
  const [failText, setFailText] = useState("");

  const submit = async () => {
    setIsLoading(true);
    try {
      const resp = await post("alerts/ask_question", {
        exam,
        question: question === "Overall Exam" ? null : question,
        message,
      });
      const data = await resp.json();
      if (!data.success) {
        throw Error();
      }
      setMessage("");
      onUpdate(data);
    } catch {
      setFailText(
        "Something went wrong. Please try again, or reload the page."
      );
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
