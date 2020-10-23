/* eslint-disable no-shadow */
import React, { useEffect, useState } from "react";
import { Col, Container, Form, Navbar, Row } from "react-bootstrap";
import EndModal from "./EndModal";
import ErrorBoundary from "./ErrorBoundary";
import Exam from "./Exam";
import ExamAlerts from "./ExamAlerts";
import ExamContext from "./ExamContext";
import InternetDown from "./InternetDown";
import NavbarWarnings from "./NavbarWarnings";
import PasswordDecryptor from "./PasswordDecryptor";
import ExamDownloader from "./ExamDownloader";
import GoogleSignInButton from "./GoogleSignInButton";
import post from "./post";
import Timer from "./Timer";

export default function StudentApp() {
  const [username, setUsername] = useState("");

  const [examList, setExamList] = useState([]);

  const forceSelectedExam = decodeURIComponent(window.location.pathname)
    .replace("/", "")
    .trim();

  const [selectedExam, setSelectedExam] = useState(forceSelectedExam);

  const [publicGroup, setPublicGroup] = useState(null);

  const [encryptedGroups, setEncryptedGroups] = useState(null);

  const [savedAnswers, setSavedAnswers] = useState(null);

  const [deadline, setDeadline] = useState(null);

  const [decryptedGroups, setDecryptedGroups] = useState(null);

  const [examLocked, setExamLocked] = useState(false);

  const [examEnded, setExamEnded] = useState(false);

  const [showInternetError, setShowInternetError] = useState(false);

  const [unsavedQuestions, setUnsavedQuestions] = useState(new Set());

  const [solvedQuestions, setSolvedQuestions] = useState(new Map());

  const [starredQuestions, setStarredQuestions] = useState(new Map());

  useEffect(() => {
    try {
      setStarredQuestions(
        new Map(JSON.parse(localStorage.getItem("starredQs")))
      );
    } catch {
      // pass
    }
  }, []);

  useEffect(() => {
    const go = async () => {
      setExamList(await (await post("list_exams")).json());
    };
    go();
  }, []);

  const handleExamSelect = (e) => {
    setSelectedExam(e.target.value);
    setEncryptedGroups(null);
  };

  const handleReceiveExam = ({
    exam,
    publicGroup,
    privateGroups,
    answers,
    deadline,
    timestamp,
  }) => {
    setSavedAnswers(answers);
    setSelectedExam(exam);
    setPublicGroup(publicGroup);
    setEncryptedGroups(privateGroups);
    setDeadline(
      deadline -
        Math.round(timestamp) +
        Math.round(new Date().getTime() / 1000) -
        2
    );
  };

  const handleLock = () => setExamLocked(true);

  const handleEnd = () => setExamEnded(true);

  return (
    <>
      <Navbar bg="dark" variant="dark" sticky="top">
        <Navbar.Brand href="#">CS 61A Exam Runner</Navbar.Brand>
        <NavbarWarnings
          unsavedQuestions={unsavedQuestions}
          solvedQuestions={solvedQuestions}
        />
        {deadline && (
          <Timer target={deadline} onLock={handleLock} onEnd={handleEnd} />
        )}
      </Navbar>
      <Container>
        <br />
        <Row>
          <Col>
            <h1>Midterm</h1>
          </Col>
        </Row>
        <Row>
          <Col>
            <GoogleSignInButton onSuccess={setUsername} />
          </Col>
        </Row>
        <br />
        {username && !encryptedGroups && !forceSelectedExam && (
          <>
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
                        <option>{exam}</option>
                      ))}
                    </Form.Control>
                  </Form.Group>
                </Form>
              </Col>
            </Row>
          </>
        )}
        {username && selectedExam && !encryptedGroups && (
          <Row>
            <Col>
              <p>
                You have selected the exam <b>{selectedExam}</b>.{" "}
                {!forceSelectedExam && (
                  <>
                    {" "}
                    If this does not look correct, please re-select your exam.
                  </>
                )}
              </p>
              <p>
                Click the button to generate your exam. You can do this before
                the exam starts.
              </p>
              <ExamDownloader
                exam={selectedExam}
                onReceive={handleReceiveExam}
              />
            </Col>
          </Row>
        )}
        {encryptedGroups && !decryptedGroups && (
          <>
            <br />
            <Row>
              <Col>
                <p>
                  The <b>{selectedExam}</b> exam has successfully been
                  downloaded! Enter the password distributed by course staff to
                  decrypt it and start the exam.
                </p>
                <PasswordDecryptor
                  encryptedExam={encryptedGroups}
                  onDecrypt={setDecryptedGroups}
                />
              </Col>
            </Row>
          </>
        )}
        <br />
        <ExamContext.Provider
          value={{
            exam: selectedExam,
            savedAnswers,
            locked: examLocked,
            onInternetError: () => setShowInternetError(true),
            recordUnsaved: (question) => {
              unsavedQuestions.add(question);
              setUnsavedQuestions(new Set(unsavedQuestions));
            },
            recordSaved: (question) => {
              unsavedQuestions.delete(question);
              setUnsavedQuestions(new Set(unsavedQuestions));
            },
            recordSolved: (question) => {
              if (!solvedQuestions.get(question)) {
                solvedQuestions.set(question, true);
                setSolvedQuestions(new Map(solvedQuestions));
              }
            },
            recordUnsolved: (question) => {
              if (
                !solvedQuestions.has(question) ||
                solvedQuestions.get(question)
              ) {
                solvedQuestions.set(question, false);
                setSolvedQuestions(new Map(solvedQuestions));
              }
            },
            unsavedQuestions,
            solvedQuestions,
            setStarred: (question, starred) => {
              starredQuestions.set(question, starred);
              setStarredQuestions(new Map(starredQuestions));
              try {
                localStorage.setItem(
                  "starredQs",
                  JSON.stringify(Array.from(starredQuestions.entries()))
                );
              } catch {
                // pass
              }
            },
            starredQuestions,
          }}
        >
          <Exam
            publicGroup={publicGroup}
            groups={decryptedGroups}
            ended={examEnded}
          />
          <ErrorBoundary>
            {encryptedGroups && <ExamAlerts exam={selectedExam} />}
          </ErrorBoundary>
        </ExamContext.Provider>
        {examLocked && <EndModal />}
        {showInternetError && (
          <InternetDown onHide={() => setShowInternetError(false)} />
        )}
      </Container>
    </>
  );
}
