import React from "react";

export default function NavbarWarnings({ unsavedQuestions, solvedQuestions }) {
  if (solvedQuestions.size === 0) {
    return null;
  }
  const solved = +Array.from(solvedQuestions.values()).reduce((x, y) => x + y);
  const total = solvedQuestions.size;
  const undisabledStyle = {
    cursor: "inherit",
    opacity: 1,
  };
  return (
    <>
      {unsavedQuestions.size ? (
        <div
          className="ml-auto btn btn-danger disabled"
          style={undisabledStyle}
        >
          {unsavedQuestions.size} unsaved question
          {unsavedQuestions.size !== 1 && "s"}
        </div>
      ) : (
        <div
          className="ml-auto btn btn-outline-light disabled"
          style={undisabledStyle}
        >
          {solved} / {total} questions solved
        </div>
      )}
    </>
  );
}
