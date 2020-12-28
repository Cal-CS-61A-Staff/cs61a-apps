import React from "react";
import TableNavButton from "./TableNavButton.js";

export default function TableNavButtons({ index, len, setIndex }) {
  return (
    <div className="TableNavButtons">
      <TableNavButton onClick={() => setIndex(0)}>{"<<"}</TableNavButton>
      <TableNavButton onClick={() => setIndex(Math.max(index - 1, 0))}>
        {"<"}
      </TableNavButton>
      <TableNavButton onClick={() => setIndex(Math.min(index + 1, len - 1))}>
        {">"}
      </TableNavButton>
      <TableNavButton onClick={() => setIndex(len - 1)}>{">>"}</TableNavButton>
    </div>
  );
}
