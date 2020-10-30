import React, { useEffect, useRef, useState } from "react";
import { Col, Modal } from "react-bootstrap";
import Button from "react-bootstrap/Button";
import Toast from "react-bootstrap/Toast";
import AlertsContext from "./AlertsContext";
import AskQuestion from "./AskQuestion";
import { getToken } from "./auth";
import post from "./post";
import StudentMessagesList from "./StudentMessagesList";
import { timeDeltaMinutesString } from "./timeUtils";
import useInterval from "./useInterval";
import useTick from "./useTick";

export default function ExamAlerts({ exam, setDeadline }) {
  const [examData, setExamData] = useState(null);
  const [stale, setStale] = useState(false);
  const [fail, setFail] = useState(false);

  const [audioQueue, setAudioQueue] = useState([]); // pop off the next audio to play
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  const [show, setShow] = useState(true);
  const [showModal, setShowModal] = useState(false);

  const announcementListRef = useRef();

  const time = useTick();

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
    (async () => {
      try {
        const resp = await post("/alerts/fetch_data", {
          token: getToken(),
          exam,
        });
        if (resp.ok) {
          const data = await resp.json();
          if (data.success) {
            setExamData(data);
          } else {
            setFail(true);
          }
        } else {
          setFail(true);
        }
      } catch {
        setFail(true);
      }
    })();
  }, []);

  useInterval(async () => {
    if (examData) {
      try {
        const resp = await post("/alerts/fetch_data", {
          token: getToken(),
          exam,
          receivedAudio: examData.announcements.map((x) => x.id),
        });
        if (resp.ok) {
          const data = await resp.json();
          if (data.success) {
            setExamData(data);
            setStale(false);
            setDeadline(
              data.endTime -
                Math.round(data.timestamp) +
                Math.round(new Date().getTime() / 1000) -
                2
            );
            const newAudio = [];
            for (const { audio } of data.announcements) {
              if (audio) {
                newAudio.push(audio);
                setShow(true);
                announcementListRef.current.scrollTop =
                  announcementListRef.current.scrollHeight;
              }
            }
            newAudio.reverse();
            setAudioQueue((queue) => queue.concat(newAudio));
          } else {
            setStale(true);
          }
        } else {
          setStale(true);
        }
      } catch (e) {
        console.error(e);
        setStale(true);
      }
    }
  }, 10000);

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
                time: announcementTime,
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
          <Modal.Header>
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
            <AskQuestion exam={exam} onUpdate={setExamData} />
            <StudentMessagesList />
          </Modal.Body>
        </Modal>
      )}
    </AlertsContext.Provider>
  );
}
