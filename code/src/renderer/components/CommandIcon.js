import React from "react";

import "@fortawesome/fontawesome-free/css/all.css";

export default function CommandIcon(props) {
  const icon = computeIcon(props.commandName);
  return (
    <span
      className={`commandIcon ${icon.className}`}
      onClick={props.onClick}
      style={{ color: icon.color, ...props.style }}
      aria-hidden
    />
  );
}

function computeIcon(name) {
  return {
    Run: { color: "green", className: "fas fa-play" },
    Test: { color: "red", className: "fas fa-graduation-cap" },
    Debug: { color: "orange", className: "fas fa-bug" },
    Stop: { color: "red", className: "fas fa-stop" },
    Restart: { color: "green", className: "fas fa-redo" },
    Prev: { color: "white", className: "far fa-arrow-alt-circle-left" },
    Next: { color: "white", className: "far fa-arrow-alt-circle-right" },
    Format: { color: "lightblue", className: "fas fa-align-left" },
  }[name];
}
