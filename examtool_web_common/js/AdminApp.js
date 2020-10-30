import React, { useEffect, useRef, useState } from "react";
import { Col, Container, Row, Form } from "react-bootstrap";

import { edit } from "ace";
import { getToken } from "./auth";
import CourseSelector from "./CourseSelector";
import GoogleSignInButton from "./GoogleSignInButton";
import LoadingButton from "./LoadingButton";
import post from "./post";

export default function AdminApp() {
  const [username, setUsername] = useState("");

  const [course, setCourse] = useState(null);

  const [examList, setExamList] = useState([]);

  const [examData, setExamData] = useState(null);

  const editorRef = useRef();

  // eslint-disable-next-line no-shadow
  const handleCourseSelect = async (course) => {
    setCourse(course);
    setExamList(
      await (await post("list_exams", { token: getToken(), course })).json()
    );
  };

  const handleExamSelect = async (exam) => {
    setExamData(
      await (await post("get_exam", { token: getToken(), course, exam })).json()
    );
  };

  useEffect(() => {
    if (document.querySelector("#editor")) {
      editorRef.current = edit("editor");
      editorRef.current.session.setMode("ace/mode/json");
      editorRef.current.setValue(JSON.stringify(examData.exam, null, "\t"));
    }
  }, [examData && examData.exam]);

  return (
    <Container>
      <br />
      <Row>
        <Col>
          <h1>Final Exam Admin Panel</h1>
        </Col>
      </Row>
      <Row>
        <Col>
          <GoogleSignInButton onSuccess={setUsername} />
        </Col>
      </Row>
      <br />
      {username && !course && (
        <Row>
          <Col>
            <CourseSelector onSuccess={handleCourseSelect} />
          </Col>
        </Row>
      )}
      {username && course && (
        <Row>
          <Col>
            Select an exam
            <Form.Control
              as="select"
              onChange={(e) => handleExamSelect(e.target.value)}
            >
              <option hidden disabled selected value="">
                Select an exam
              </option>
              {examList && examList.map((exam) => <option>{exam}</option>)}
            </Form.Control>
          </Col>
        </Row>
      )}
      {examData && (
        <>
          <br />
          <Row>
            <Col>
              <div id="editor" style={{ width: "100%", height: 1000 }} />
            </Col>
            <Col>
              Secret:
              <code>{examData.secret}</code>
              <LoadingButton>Regenerate</LoadingButton>
            </Col>
          </Row>
        </>
      )}
    </Container>
  );
}
