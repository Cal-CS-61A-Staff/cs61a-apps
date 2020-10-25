import React, { useEffect, useState } from "react";
import { Col, Container, Form, Row } from "react-bootstrap";
import AlertsContext from "./AlertsContext";
import AskQuestion from "./AskQuestion";
import { getToken } from "./auth";
import ConnectAlertButton from "./ConnectAlertButton";
import CreateAnnouncement from "./CreateAnnouncement";
import GoogleSignInButton from "./GoogleSignInButton";
import post from "./post";
import StaffAlertsList from "./StaffAlertsList";
import StaffMessagesList from "./StaffMessagesList";
import StudentMessagesList from "./StudentMessagesList";
import StudentAlertsList from "./StudentAlertsList";
import TimerBanner from "./TimerBanner";
import useInterval from "./useInterval";
import useTick from "./useTick";

export default function Alerts() {
  const [username, setUsername] = useState("");
  const [examList, setExamList] = useState([]);
  const forceSelectedExam = decodeURIComponent(window.location.pathname)
    .replace("/", "")
    .trim();
  const [selectedExam, setSelectedExam] = useState(forceSelectedExam);
  const [examData, setExamData] = useState(null);
  const [stale, setStale] = useState(false);

  const [isStaff, setIsStaff] = useState(false);
  const [staffData, setStaffData] = useState(null);

  const [audioQueue, setAudioQueue] = useState([]); // pop off the next audio to play
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

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
    if (audioQueue.length > 0 && !isPlayingAudio) {
      const nextAudio = audioQueue[0];
      const sound = new Audio(`data:audio/mp3;base64,${nextAudio}`);
      setIsPlayingAudio(true);
      sound.play();
      sound.addEventListener("ended", () => {
        setAudioQueue((queue) => queue.slice(1));
        setIsPlayingAudio(false);
      });
    }
  }, [audioQueue, isPlayingAudio]);

  useEffect(() => {
    document.title = stale
      ? "(DISCONNECTED) Exam Announcements"
      : "Exam Announcements";
  }, [stale]);

  useInterval(async () => {
    if (examData || staffData) {
      try {
        const resp = await post(examData ? "fetch_data" : "fetch_staff_data", {
          token: getToken(),
          exam: selectedExam,
          receivedAudio: examData
            ? examData.announcements.map((x) => x.id)
            : null,
        });
        if (resp.ok) {
          const data = await resp.json();
          if (data.success) {
            setStale(false);
            if (examData) {
              setExamData(data);
              const newAudio = [];
              for (const { audio } of data.announcements) {
                if (audio) {
                  newAudio.push(audio);
                }
              }
              newAudio.reverse();
              setAudioQueue((queue) => queue.concat(newAudio));
            } else {
              setStaffData(data);
            }
          }
        }
      } catch (e) {
        console.error(e);
        setStale(true);
      }
    }
  }, 10000);

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
        {username && !examData && !staffData && !forceSelectedExam && (
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
        {username && selectedExam && !examData && !staffData && (
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
                onReceive={isStaff ? setStaffData : setExamData}
              />
            </Col>
          </Row>
        )}
        {examData && (
          <Row>
            <Col>
              <TimerBanner data={examData} />
            </Col>
          </Row>
        )}
        {examData && (
          <Row>
            <Col>
              <StudentAlertsList />
            </Col>
            <Col>
              <AskQuestion onUpdate={setExamData} exam={selectedExam} />
              <StudentMessagesList />
            </Col>
          </Row>
        )}
        <CreateAnnouncement
          exam={selectedExam}
          staffData={staffData}
          onUpdate={setStaffData}
        />
        {staffData && (
          <Row>
            <Col>
              <StaffAlertsList
                selectedExam={selectedExam}
                staffData={staffData}
                onUpdate={setStaffData}
              />
            </Col>
            <Col>
              <StaffMessagesList
                selectedExam={selectedExam}
                staffData={staffData}
                onUpdate={setStaffData}
              />
            </Col>
          </Row>
        )}
        <br />
      </Container>
    </AlertsContext.Provider>
  );
}
