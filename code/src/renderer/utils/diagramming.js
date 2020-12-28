import $ from "jquery";

export function getDims() {
  const parentElement = document.body;
  const div = document.createElement("div");
  $(div).css("position", "absolute");
  $(div).css("white-space", "pre-line");
  $(div).css("font-family", "Monaco, monospace");
  $(div).css("font-size", "14px");

  div.innerHTML = "x".repeat(999) + "x\n".repeat(1000);
  parentElement.appendChild(div);
  const w = div.offsetWidth / 1000;
  const h = div.offsetHeight / 1001;
  parentElement.removeChild(div);
  return [w, h];
}

const charWidth = getDims()[0];

let depthToArrows = {};

export const minWidth = charWidth * 4 + 5;

function calcContentLength(elem) {
  if (elem[0] === "ref") {
    return minWidth;
  } else {
    return Math.max(minWidth, charWidth * elem[1].length + 10);
  }
}

function straightArrow(container, x1, y1, x2, y2, color) {
  container
    .circle(5)
    .dx(x1 - 5 / 2)
    .dy(y1 - 5 / 2)
    .fill(color);
  container
    .polygon("0,0 -10,5 -10,-5")
    .fill(color)
    .dx(x2)
    .dy(y2)
    .rotate((180 / Math.PI) * Math.atan2(y2 - y1, x2 - x1), x2, y2);
  const length = Math.hypot(x2 - x1, y2 - y1);
  container
    .line(x1, y1, x2 + ((x1 - x2) / length) * 5, y2 + ((y1 - y2) / length) * 5)
    .stroke({ width: 2, color });
}

function branchArrow(container, x1, y1, x2, y2, color) {
  container
    .polygon("0,0 -10,5 -10,-5")
    .fill(color)
    .dx(x2)
    .dy(y2)
    .rotate((180 / Math.PI) * Math.atan2(y2 - y1, x2 - x1), x2, y2);
  const length = Math.hypot(x2 - x1, y2 - y1);
  container
    .line(x1, y1, x2 + ((x1 - x2) / length) * 5, y2 + ((y1 - y2) / length) * 5)
    .stroke({ width: 2, color });
}

/* eslint-disable no-param-reassign */
function curvedArrow(container, x1, y1, x2, y2, color, depth) {
  if (y1 !== y2 || x1 === x2 + minWidth / 2) {
    straightArrow(container, x1, y1, x2, y2, color);
  } else {
    if (depthToArrows[depth] === undefined) {
      depthToArrows[depth] = 1;
    } else {
      depthToArrows[depth] += 1;
    }
    const offset = 10;
    container
      .circle(5)
      .dx(x1 - 5 / 2)
      .dy(y1 - 5 / 2)
      .fill(color);
    container
      .polygon("0,0 -4,4 -4,-4")
      .fill(color)
      .dx(x2 + minWidth / 2)
      .dy(y2 - minWidth / 2)
      .rotate(90, x2 + minWidth / 2, y2 - minWidth / 2);
    container
      .line(x1, y1, x1, y1 - minWidth / 2 - offset)
      .stroke({ width: 2, color });
    container
      .line(
        x1,
        y1 - minWidth / 2 - offset,
        x2 + minWidth / 2,
        y2 - minWidth / 2 - offset
      )
      .stroke({ width: 2, color });
    container
      .line(
        x2 + minWidth / 2,
        y2 - minWidth / 2 - offset,
        x2 + minWidth / 2,
        y2 - minWidth / 2
      )
      .stroke({ width: 2, color });
  }
}
/* eslint-enable no-param-reassign */

export function displayTree(data, container) {
  const indents = [10];
  const levelHeight = 80;

  function displayTreeWorker(tr, depth, prevX, prevY) {
    const label = tr[0];
    const branches = tr.length > 1 ? tr[1] : [];
    const x1 = indents[depth];
    const y1 = 10 + depth * levelHeight;

    const elemWidth = Math.max(50, charWidth * label.toString().length + 40);

    if (prevX != null && prevY != null) {
      branchArrow(container, prevX, prevY, x1 + elemWidth / 2, y1, "white");
    }

    // circle
    container
      .rect(elemWidth, 50)
      .radius(50)
      .dx(x1)
      .dy(y1)
      .stroke({ color: "white", width: 2 })
      .fill("transparent")
      .back();
    // label
    container
      .text(label)
      .dx(x1 + 20)
      .dy(y1 + 12)
      .fill({ color: "white" })
      .font("family", "Monaco, monospace")
      .font("size", 14);

    indents[depth] += elemWidth + 30;
    // if there are branches, recurse.
    if (branches.length > 0) {
      indents.push(10);
      for (let i = 0; i < branches.length; i++) {
        displayTreeWorker(branches[i], depth + 1, x1 + elemWidth / 2, y1 + 50);
      }
    }
  }

  displayTreeWorker(data, 0);
}

export function displayElem(
  x,
  y,
  id,
  allData,
  container,
  depth,
  cache,
  color,
  x1 = false,
  y1 = false
) {
  if (id[0] === "ref") {
    const data = allData[id[1]];

    if (!x1) {
      // eslint-disable-next-line no-param-reassign
      x1 = x + minWidth / 2;
      // eslint-disable-next-line
      y1 = y + minWidth / 2;
    }
    if (cache.has(id[1])) {
      curvedArrow(container, x1, y1, ...cache.get(id[1]), color, depth);
      return 0;
    }
    let x2;
    let y2;
    if (depth === 0) {
      cache.set(id[1], [x, y]);
      x2 = x + minWidth + 15;
      y2 = y + minWidth / 2;
      // eslint-disable-next-line no-param-reassign
      x = x2;
    } else {
      x2 = x + minWidth / 2;
      y2 = y + (minWidth + 15) * depth;
      // eslint-disable-next-line no-param-reassign
      y = y2;
    }

    let content;
    if (data[0] === "list") {
      [, content] = data;
    } else {
      content = [data[1]];
    }
    if (data[0] === "atomic") {
      straightArrow(container, x1, y1, x, y + minWidth / 2, color);
    } else {
      straightArrow(container, x1, y1, x2, y2, color);
    }
    cache.set(id[1], [x, y + minWidth / 2]);

    let pos = 0;
    const lens = [];
    for (const elem of content) {
      lens.push(pos);
      pos += calcContentLength(elem);
    }

    let newDepth = 0;
    for (let i = content.length - 1; i >= 0; --i) {
      if (i !== 0) {
        container
          .line(x + lens[i], y, x + lens[i], y + minWidth)
          .stroke({ color, width: 2 });
      }
      const elem = content[i];
      if (
        i !== content.length - 1 &&
        elem[0] === "ref" &&
        !cache.has(elem[1])
      ) {
        newDepth += 1;
      }
      newDepth += displayElem(
        x + lens[i],
        y,
        elem,
        allData,
        container,
        newDepth,
        cache,
        color
      );
    }

    if (data[0] === "promise") {
      container
        .circle(minWidth)
        .dx(x)
        .dy(y)
        .stroke({ color, width: 2 })
        .fill("transparent")
        .back();
    } else if (data[0] === "list") {
      container
        .rect(pos, minWidth)
        .dx(x)
        .dy(y)
        .stroke({ color, width: 2 })
        .fill("transparent")
        .back();
    }
    // container.text(newDepth.toString(10)).dx(x).dy(y);
    depthToArrows = {};
    return newDepth;
  } else if (id[0] === "empty") {
    container
      .line(x, y + minWidth, x + minWidth, y)
      .stroke({ width: 2, color });
    return 0;
  } else {
    const width = calcContentLength(id);
    container
      .text(id[1])
      .fill(color)
      .font("family", "Monaco, monospace")
      .font("size", 14)
      .cx(x + width / 2)
      .cy(y + minWidth / 2);
    // container.text("0").dx(x).dy(y);
    return 0;
  }
}
