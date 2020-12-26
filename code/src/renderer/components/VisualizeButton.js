import React from "react";

export default function VisualizeButton({ children, onClick }) {
  return (
    <button className="VisualizeButton" type="button" onClick={onClick}>
      {children}
    </button>
  );
}
