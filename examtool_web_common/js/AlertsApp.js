import React, { useEffect, useState } from "react";
import { Col, Container, Form, Row } from "react-bootstrap";
import AlertsContext from "./AlertsContext";
import AskQuestion from "./AskQuestion";
import ConnectAlertButton from "./ConnectAlertButton";
import CreateAnnouncement from "./CreateAnnouncement";
import GoogleSignInButton from "./GoogleSignInButton";
import post from "./post";
import StaffAlertsList from "./StaffAlertsList";
import StaffMessagesList from "./StaffMessagesList";
import StudentMessagesList from "./StudentMessagesList";
import StudentAlertsList from "./StudentAlertsList";
import TimerBanner from "./TimerBanner";
import useExamAlertsData from "./useExamAlertsData";
import useTick from "./useTick";

export default function Alerts() {
  const [username, setUsername] = useState("");
  const [examList, setExamList] = useState([]);
  const forceSelectedExam = decodeURIComponent(window.location.pathname)
    .replace("/", "")
    .trim();
  const [selectedExam, setSelectedExam] = useState(forceSelectedExam);

  const [isStaff, setIsStaff] = useState(false);

  const [examData, stale, onConnect, send] = useExamAlertsData(
    selectedExam,
    isStaff
  );

  const time = useTick();

  const handleExamSelect = (e) => {
    setSelectedExam(e.target.value);
  };

  useEffect(() => {
    (async () => {
      setExamList(await (await post("list_exams")).json());
    })();
  }, []);

  useEffect(() => {
    document.title = stale
      ? "(DISCONNECTED) Exam Announcements"
      : "Exam Announcements";
  }, [stale]);

  return (
    <AlertsContext.Provider value={{ time, examData, stale }}>
      <Container>
        <br />
        <Row>
          <Col>
            <h1>Exam Announcements</h1>
          </Col>
        </Row>
        <Row>
          <Col>
            <GoogleSignInButton onSuccess={setUsername} />
          </Col>
        </Row>
        <br />
        {username && !examData && !forceSelectedExam && (
          <Row>
            <Col>
              <Form>
                <Form.Group controlId="exampleForm.SelectCustom">
                  <Form.Label>Now, choose your exam:</Form.Label>
                  <Form.Control
                    as="select"
                    value={selectedExam}
                    onChange={handleExamSelect}
                    custom
                  >
                    <option hidden disabled selected value="">
                      Select an exam
                    </option>
                    {examList.map((exam) => (
                      <option key={exam}>{exam}</option>
                    ))}
                  </Form.Control>
                </Form.Group>
                <Form.Group>
                  <Form.Check
                    id="staffCheckbox"
                    custom
                    type="checkbox"
                    label="Log in as staff"
                    value={isStaff}
                    onChange={(e) => setIsStaff(e.target.checked)}
                  />
                </Form.Group>
              </Form>
            </Col>
          </Row>
        )}
        {username && selectedExam && !examData && (
          <Row>
            <Col>
              <p>
                You have selected the exam <b>{selectedExam}</b>.
                {!forceSelectedExam && (
                  <>
                    {" "}
                    If this does not look correct, please re-select your exam.
                  </>
                )}
              </p>
              <p>
                Click the button to connect to the exam server. You can do this
                before the exam begins.
              </p>
              <ConnectAlertButton
                exam={selectedExam}
                isStaff={isStaff}
                onDownloadClick={onConnect}
              />
            </Col>
          </Row>
        )}
        {!isStaff && examData && (
          <Row>
            <Col>
              <TimerBanner data={examData} />
            </Col>
          </Row>
        )}
        {!isStaff && examData && (
          <Row>
            <Col>
              <StudentAlertsList />
            </Col>
            {examData.enableClarifications === true && (
              <Col xs={6}>
                <AskQuestion send={send} />
                <StudentMessagesList />
              </Col>
            )}
          </Row>
        )}
        {isStaff && examData && (
          <CreateAnnouncement staffData={examData} send={send} />
        )}
        {isStaff && examData && (
          <Row>
            <Col xs={6}>
              <StaffAlertsList staffData={examData} send={send} />
            </Col>
            <Col xs={6}>
              <StaffMessagesList
                selectedExam={selectedExam}
                staffData={examData}
                send={send}
              />
            </Col>
          </Row>
        )}
        <br />
      </Container>
    </AlertsContext.Provider>
  );
}
