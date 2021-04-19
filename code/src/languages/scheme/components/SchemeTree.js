import * as React from "react";
import { getDims } from "../../../renderer/utils/diagramming.js";
import SVGCanvas from "../../../renderer/components/SVGCanvas.js";

const UNEVALUATED = 0;
const EVALUATING = 1;
const APPLYING = 2;
const EVALUATED = 3;

const charHeight = getDims()[1];
const charWidth = getDims()[0];

function getDataAtIndex(data, i) {
  const labels = [
    ["transitions", "transition_type"],
    ["strs", "str"],
    ["parent_strs", "parent_str"],
  ];
  const out = {};
  const transitionTime = {};
  for (const label of labels) {
    for (const val of data[label[0]]) {
      if (val[0] > i) {
        break;
      }
      [transitionTime[label[1]], out[label[1]]] = val;
    }
  }

  let j;

  for (j = 0; j < data.children.length - 1; ++j) {
    if (data.children[j + 1][0] > i) {
      break;
    }
  }

  out.children = [];
  for (const child of data.children[j][1]) {
    out.children.push(getDataAtIndex(child, i));
  }

  return out;
}

function displayTreeWorker(data, container, x, y, level, starts) {
  let color;
  switch (data.transition_type) {
    case UNEVALUATED:
      color = "#536dff";
      break;
    case EVALUATING:
      color = "#ff0f00";
      break;
    case EVALUATED:
      color = "#44ff51";
      break;
    case APPLYING:
      color = "#ffa500";
      break;
    default:
      throw Error(`Unexpected transition: ${data.transition_type}`);
  }

  container
    .rect(data.str.length * charWidth + 10, charHeight + 10)
    .dx(x - 5)
    .dy(y)
    .stroke({ color, width: 2 })
    .fill({ color: "#FFFFFF" })
    .radius(10);

  container
    .text(data.str)
    .font("family", "Monaco, monospace")
    .font("size", 14)
    .dx(x)
    .dy(y);
  let xDelta = charWidth;

  // eslint-disable-next-line no-param-reassign
  starts[level] = x + charWidth * (data.str.length + 1);
  for (const child of data.children) {
    if (starts.length === level + 1) {
      starts.push([10]);
    }
    const parentLen = child.parent_str.length * charWidth;
    container
      .line(
        x + xDelta + parentLen / 2,
        y + charHeight + 5,
        Math.max(x + xDelta - 100000, starts[level + 1]) +
          (child.str.length * charWidth) / 2 +
          5,
        y + 60
      )
      .stroke({ width: 3, color: "#c8c8c8" })
      .back();
    displayTreeWorker(
      child,
      container,
      Math.max(x + xDelta - 100000, starts[level + 1]),
      y + 50,
      level + 1,
      starts
    );
    xDelta += parentLen + charWidth;
  }
}

function displayTree(svg, index, allData) {
  let currData;
  for (const data of allData) {
    if (data[0] > index) {
      break;
    }
    [, currData] = data;
  }
  const data = getDataAtIndex(currData, index);

  displayTreeWorker(data, svg, 10, 15, 0, [0]);
}

export default function SchemeTree({ index, data }) {
  return <SVGCanvas draw={(svg) => displayTree(svg, index, data)} />;
}
