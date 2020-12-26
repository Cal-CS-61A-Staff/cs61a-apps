import * as React from "react";
import StdoutElem from "./StdoutElem.js";
import OutputDrawElem from "./OutputDrawElem.js";
import TableVisualization from "./TableVisualization.js";

const DRAW_MARKER = "DRAW: ";

export default function OutputElem(props) {
  if (props.text.startsWith(DRAW_MARKER)) {
    try {
      return (
        <OutputDrawElem
          data={JSON.parse(props.text.substr(DRAW_MARKER.length))}
        />
      );
    } catch (e) {
      throw e;
    }
  }

  const { __html: html, visualization } = props.text;

  if (html) {
    // eslint-disable-next-line react/no-danger
    return <div dangerouslySetInnerHTML={props.text} />;
  } else if (visualization) {
    return <TableVisualization data={visualization} />;
  }
  return <StdoutElem text={props.text} lang={props.lang} type={props.type} />;
}
