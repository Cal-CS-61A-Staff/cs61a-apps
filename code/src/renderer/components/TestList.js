import React from "react";
import TestGroup from "./TestGroup";

export default function TestList(props) {
  const problems = {};
  for (const elem of props.data) {
    if (!problems[elem.name[0]]) {
      problems[elem.name[0]] = [];
    }
    problems[elem.name[0]].push(elem);
  }
  return (
    <div className="testList">
      {Object.keys(problems).map((problem) => (
        <TestGroup
          key={problem}
          name={problem}
          onProblemClick={props.onProblemClick}
          onTestClick={props.onTestClick}
          selectedProblem={props.selectedProblem}
          selectedTest={props.selectedTest}
        >
          {problems[problem]}
        </TestGroup>
      ))}
    </div>
  );
}
