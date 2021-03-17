import React, { useEffect, useRef, useState } from "react";
import {
  Button,
  ButtonGroup,
  Col,
  Container,
  Row,
  Form,
} from "react-bootstrap";

import { edit } from "ace";
import Exam from "./Exam";
import FailText from "./FailText";
import LoadingButton from "./LoadingButton";
import post from "./post";

import sampleExam from "./sampleExam.md";

export default function StaffApp() {
  const [exam, setExam] = useState(null);
  const [failText, setFailText] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("live");
  const [draft, setDraft] = useState(false);
  const [seed, setSeed] = useState("");

  const editorRef = useRef();

  useEffect(() => {
    editorRef.current = edit("editor");
    editorRef.current.session.setMode("ace/mode/markdown");
    editorRef.current.setValue(sampleExam);
  }, []);

  const generate = async () => {
    const text = editorRef.current.getValue();
    setLoading(true);
    const ret = await post("convert", { text, draft, seed }, true);
    setLoading(false);
    if (!ret.ok) {
      return;
    }
    const { success, examJSON, error } = await ret.json();
    if (success) {
      setExam(JSON.parse(examJSON));
      setFailText("");
    } else {
      setExam(null);
      setFailText(error);
    }
  };

  // eslint-disable-next-line no-unused-vars
  const renderPDF = () => {
    const form = document.createElement("form");
    form.action = "/render";
    form.method = "POST";
    form.target = "_blank";
    const input = document.createElement("input");
    input.name = "exam";
    input.value = JSON.stringify(exam);
    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
  };

  return (
    <Container fluid>
      <br />
      <Row>
        <Col>
          <h1>Exam Generator</h1>
          <div id="editor" style={{ width: "100%", height: 1000 }} />
        </Col>
        <Col>
          <LoadingButton
            primary
            onClick={generate}
            loading={loading}
            disabled={loading}
          >
            Generate
          </LoadingButton>
          <ButtonGroup
            style={{ marginLeft: "10px" }}
            aria-label="Basic example"
          >
            <Button variant="secondary" onClick={() => setMode("live")}>
              Live Exam
            </Button>
            {/* <Button variant="secondary" onClick={renderPDF}>PDF</Button> */}
            <Button variant="secondary" onClick={() => setMode("json")}>
              JSON
            </Button>
          </ButtonGroup>
          <span className="ml-3">
            <Form.Check
              id="draftCheckbox"
              checked={draft}
              onChange={(e) => setDraft(e.target.checked)}
              custom
              inline
              type="checkbox"
              label="Draft mode (fast, but less accurate)"
            />
          </span>
          <span className="ml-3">
            <Form.Control
              id="draftCheckbox"
              value={seed}
              placeholder="Scrambling seed"
              onChange={(e) => setSeed(e.target.value)}
              custom
              inline
              type="text"
            />
          </span>
          <FailText text={failText} />
          <br />
          <div
            style={{
              height: 900,
              overflow: "auto",
              border: "2px solid black",
              padding: 10,
            }}
          >
            {mode === "live" && exam && (
              <Exam
                groups={exam.groups}
                publicGroup={exam.public}
                watermark={exam.watermark}
              />
            )}
            {mode === "json" && (
              <textarea
                style={{
                  width: "100%",
                  height: "100%",
                  whiteSpace: "pre-wrap",
                }}
                readOnly
                value={JSON.stringify(exam, null, "\t")}
              />
            )}
          </div>
        </Col>
      </Row>
    </Container>
  );
}
