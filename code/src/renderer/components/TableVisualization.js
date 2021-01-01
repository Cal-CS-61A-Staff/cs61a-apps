import React, { useState } from "react";
import VisualizeButton from "./VisualizeButton.js";
import TableNavButtons from "./TableNavButtons.js";

export default function TableVisualization({ data }) {
  const [index, setIndex] = useState(0);
  const [expanded, setExpanded] = useState(false);
  if (!expanded) {
    return (
      <VisualizeButton onClick={() => setExpanded(true)}>
        Step-By-Step
      </VisualizeButton>
    );
  }
  return (
    <div className="TableVisualization">
      <TableNavButtons len={data.length} index={index} setIndex={setIndex} />
      <VisualizeButton onClick={() => setExpanded(false)}>Hide</VisualizeButton>
      {/* eslint-disable-next-line react/no-danger */}
      <div dangerouslySetInnerHTML={{ __html: data[index] }} />
    </div>
  );
}
