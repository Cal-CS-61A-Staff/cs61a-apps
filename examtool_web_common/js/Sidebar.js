/* eslint-disable react/no-array-index-key */
import React, { useContext } from "react";
import { Nav } from "react-bootstrap";
import ExamContext from "./ExamContext";

const star = <span style={{ color: "orange" }}> &#9733;</span>;
const check = <span> &#10003;</span>;

export default function Sidebar({ groups }) {
  const examContext = useContext(ExamContext);

  return (
    <Nav defaultActiveKey="/home" className="flex-column">
      {groups.map((group, i) => {
        const heading = (
          <Nav.Link href={`#${i + 1}`}>
            {i + 1}
            {". "}
            {group.name}
            {isCompleted(group, examContext).completed && check}
          </Nav.Link>
        );
        return (
          <div key={i}>
            {heading}
            {getAllElements(group)
              .filter(
                ({ element: { id }, name }) =>
                  name.split(".").length === 2 ||
                  examContext.starredQuestions.get(id)
              )
              .map(({ element, name }, j) => (
                <QuestionLink
                  key={j}
                  question={element}
                  name={`${i + 1}${name}`}
                />
              ))}
          </div>
        );
      })}
    </Nav>
  );
}

function QuestionLink({ question, name }) {
  const examContext = useContext(ExamContext);

  const { completed, starred } = isCompleted(question, examContext);

  const body = (
    <Nav.Link style={{ paddingLeft: 20 }} href={`#${name}`}>
      Q{name}
      {starred && star}
      {completed && !starred && check}
    </Nav.Link>
  );

  if (starred) {
    return <b>{body}</b>;
  } else if (completed) {
    return <>{body}</>;
  } else {
    return body;
  }
}

function isCompleted(question, examContext) {
  let completed = true;
  const starred = examContext.starredQuestions.get(question.id);

  const explore = (element) => {
    if (
      element.id &&
      (!examContext.solvedQuestions.get(element.id) ||
        examContext.unsavedQuestions.has(element.id) ||
        examContext.starredQuestions.get(element.id))
    ) {
      completed = false;
    } else if (element.elements) {
      for (const child of element.elements) {
        explore(child);
      }
    }
  };

  explore(question);

  return { completed, starred };
}

function getAllElements(root) {
  const out = [];

  const explore = (element, name) => {
    out.push({ element, name });
    if (element.elements) {
      element.elements.forEach((elem, i) => explore(elem, `${name}.${i + 1}`));
    }
  };

  explore(root, "");

  return out;
}
