import React, { useEffect } from "react";
import { typeset } from "MathJax";
import { Col, Jumbotron, Row } from "react-bootstrap";
import Anchor from "./Anchor";
import Points from "./Points";
import Question from "./Question";
import Sidebar from "./Sidebar";

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

export default function Exam({ groups, publicGroup, ended }) {
  useEffect(postRenderFormat, [groups, publicGroup]);

  const stickyStyle = {
    position: "sticky",
    top: "5em",
    height: "85vh",
    overflowY: "auto",
  };

  return (
    <div className="exam">
      <Row>
        <Col md={9} sm={12}>
          {!ended && publicGroup && <Group group={publicGroup} number={0} />}
          {!ended &&
            groups &&
            groups.map((group, i) => <Group group={group} number={i + 1} />)}
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
        {!ended && groups && !!groups.length && (
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
            <Group group={element} number={`${number}.${i + 1}`} small />
          ) : (
            <Question question={element} number={`${number}.${i + 1}`} />
          )
        )}
      </div>
      {!small && <hr />}
    </>
  );
}
