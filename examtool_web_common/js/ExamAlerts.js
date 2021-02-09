import React, { useEffect, useRef, useState } from "react";
import { Modal } from "react-bootstrap";
import Button from "react-bootstrap/Button";
import Toast from "react-bootstrap/Toast";
import AlertsContext from "./AlertsContext";
import AskQuestion from "./AskQuestion";
import StudentMessagesList from "./StudentMessagesList";
import { timeDeltaMinutesString } from "./timeUtils";
import useExamAlertsData from "./useExamAlertsData";
import useTick from "./useTick";

export default function ExamAlerts({ exam, setDeadline }) {
  const [examData, stale, onConnect, send] = useExamAlertsData(
    exam,
    false,
    setDeadline
  );

  const [fail, setFail] = useState(false);

  const [show, setShow] = useState(true);
  const [showModal, setShowModal] = useState(false);

  const announcementListRef = useRef();

  const time = useTick();

  useEffect(() => {
    onConnect().then((err) => !err || setFail(true));
  }, []);

  return (
    <AlertsContext.Provider value={{ time, examData, stale }}>
      <div
        ref={announcementListRef}
        style={{
          position: "fixed",
          overflow: "auto",
          bottom: 80,
          right: 32,
          width: 350,
          maxHeight: "80%",
        }}
      >
        {show &&
          examData &&
          examData.announcements
            .slice()
            .reverse()
            .map(
              ({
                id,
                message,
                question,
                timestamp: announcementTime,
                private: isPrivate,
              }) => (
                <Toast key={id}>
                  <Toast.Header closeButton={false}>
                    <strong className="mr-auto">
                      {isPrivate ? (
                        "Staff Reply"
                      ) : (
                        <>Announcement for {question}</>
                      )}
                    </strong>
                    <small>
                      {timeDeltaMinutesString(time - announcementTime)}
                    </small>
                  </Toast.Header>
                  <Toast.Body>
                    <div style={{ whiteSpace: "pre-wrap" }}>{message}</div>
                  </Toast.Body>
                </Toast>
              )
            )}
      </div>
      <div
        style={{
          position: "fixed",
          bottom: 32,
          right: 32,
          width: 350,
          background: "white",
        }}
      >
        <Button
          block
          onClick={() => setShow((x) => !x)}
          variant="outline-secondary"
        >
          {show ? "Hide Announcements" : "Show Announcements"}
          {stale ? " (Offline)" : ""}
          {examData ? "" : " (Loading...)"}
        </Button>
      </div>
      {examData && examData.enableClarifications && (
        <div
          style={{
            position: "fixed",
            bottom: 32,
            left: 32,
            width: 200,
            background: "white",
          }}
        >
          <Button
            block
            onClick={() => setShowModal(true)}
            variant="outline-secondary"
          >
            Clarifications
          </Button>
        </div>
      )}
      {fail && (
        <Modal show>
          <Modal.Header closeButton>
            <Modal.Title>Network Connection Lost!</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            The tool was unable to fetch announcements from the server. Please
            refresh and try again. If this error persists, contact your course
            staff.
          </Modal.Body>
        </Modal>
      )}
      {examData && examData.enableClarifications && (
        <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
          <Modal.Header closeButton>Ask a question</Modal.Header>
          <Modal.Body>
            <AskQuestion exam={exam} send={send} />
            <StudentMessagesList />
          </Modal.Body>
        </Modal>
      )}
    </AlertsContext.Provider>
  );
}
