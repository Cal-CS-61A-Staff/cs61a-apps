import React from "react";

export default function SuccessIcon(props) {
  if (props.none) {
    return (
      <i
        className="fas fa-question-circle"
        style={{ color: "white", ...props.style }}
      />
    );
  } else if (props.success) {
    return (
      <i
        className="fas fa-check"
        style={{ color: "lightgreen", ...props.style }}
      />
    );
  } else {
    return (
      <i
        className="fas fa-exclamation-triangle"
        style={{ color: "orange", ...props.style }}
      />
    );
  }
}
