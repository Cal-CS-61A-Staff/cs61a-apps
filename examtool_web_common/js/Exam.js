/* eslint-disable react/no-array-index-key */
import React, { useContext, useEffect } from "react";
import { typeset } from "MathJax";
import { Col, Jumbotron, Row } from "react-bootstrap";
import Anchor from "./Anchor";
import { getAuthParams, getLoginAsParams, inAdminMode } from "./auth";
import ExamContext from "./ExamContext";
import Points from "./Points";
import post from "./post";
import Question from "./Question";
import Sidebar from "./Sidebar";
import useInterval from "./useInterval";
import { synchronize } from "./logger.js";
import useStyleWatcher from "./useStyleWatcher";

export function postRenderFormat() {
  for (const link of document.getElementsByTagName("a")) {
    if (
      link.getAttribute("href") &&
      link.hostname !== window.location.hostname
    ) {
      link.target = "_blank";
    }
  }
  for (const table of document.getElementsByTagName("table")) {
    table.classList.add("table", "table-bordered");
  }
  for (const blockquote of document.getElementsByTagName("blockquote")) {
    blockquote.classList.add("blockquote");
  }
  typeset();
}

export default function Exam({ groups, publicGroup, watermark, ended }) {
  const { exam } = useContext(ExamContext);

  useEffect(postRenderFormat, [groups, publicGroup]);

  const examDivRef = useStyleWatcher(() => {
    if (watermark) {
      post("/log_event", {
        exam,
        event: "style_edited",
        ...getAuthParams(),
      });
      alert(
        "You must not edit the DOM during the exam. This is considered academic dishonesty." +
          " This event has been logged. We will follow up with you after the exam regarding this" +
          " event."
      );
    }
  }, [watermark]);

  const stickyStyle = {
    position: "sticky",
    top: "5em",
    height: "85vh",
    overflowY: "auto",
  };

  useInterval(() => {
    if (exam && !getLoginAsParams().loginas) {
      synchronize(exam);
    }
  }, 30 * 1000);

  const showExam = !ended || inAdminMode();

  return (
    <div
      className="exam"
      ref={examDivRef}
      style={
        watermark
          ? {
              backgroundImage: `url("/watermark.svg?seed=${watermark.value}&brightness=${watermark.brightness}")`,
              backgroundRepeat: "repeat-xy",
              textShadow: "0px 0px 2px white",
            }
          : {}
      }
    >
      <Row>
        <Col md={9} sm={12}>
          {showExam && publicGroup && <Group group={publicGroup} number={0} />}
          {showExam &&
            groups &&
            groups.map((group, i) => (
              <Group key={i} group={group} number={i + 1} />
            ))}
          {groups && (
            <Jumbotron>
              {/* eslint-disable-next-line jsx-a11y/accessible-emoji */}
              <h1>🎉Congratulations!🎉</h1>
              <p>
                You have reached the end of the exam! Your answers will all be
                automatically saved.
              </p>
            </Jumbotron>
          )}
        </Col>
        {showExam && groups && !!groups.length && (
          <Col md={3} className="d-none d-md-block" style={stickyStyle}>
            <Sidebar groups={groups} />
          </Col>
        )}
      </Row>
    </div>
  );
}

export function Group({ group, number, small }) {
  // eslint-disable-next-line react/jsx-props-no-spreading,jsx-a11y/heading-has-content
  const Header = (props) => (small ? <h4 {...props} /> : <h3 {...props} />);
  return (
    <>
      <br />
      <div>
        <Anchor name={number} />
        <Header style={{ marginBottom: 0 }}>
          <b>Q{number}</b> {group.name}
        </Header>
        <Points points={group.points} />
        {/* eslint-disable-next-line react/no-danger */}
        <div dangerouslySetInnerHTML={{ __html: group.html }} />
        {group.elements.map((element, i) =>
          element.type === "group" ? (
            <Group
              key={i}
              group={element}
              number={`${number}.${i + 1}`}
              small
            />
          ) : (
            <Question
              key={i}
              question={element}
              number={`${number}.${i + 1}`}
            />
          )
        )}
      </div>
      {!small && <hr />}
    </>
  );
}
