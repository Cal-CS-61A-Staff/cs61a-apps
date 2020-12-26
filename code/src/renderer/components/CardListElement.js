import React from "react";

export default function CardListElement({ name, selected, onClick }) {
  return (
    <div
      className="fileCard"
      onClick={onClick}
      style={selected ? { background: "darkslategrey" } : {}}
    >
      {name}
    </div>
  );
}
