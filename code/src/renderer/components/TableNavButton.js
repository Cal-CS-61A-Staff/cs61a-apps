import React from "react";

export default function TableNavButton({ children, onClick }) {
  return (
    <button className="TableNavButton" type="button" onClick={onClick}>
      {children}
    </button>
  );
}
