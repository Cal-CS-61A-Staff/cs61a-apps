import * as React from "react";
import SVG from "svg.js";
import svgPanZoom from "svg-pan-zoom/dist/svg-pan-zoom.min.js";

import {
  displayElem,
  getDims,
  minWidth,
} from "../../../renderer/utils/diagramming.js";

const charWidth = getDims()[0];
const charHeight = getDims()[1];

function displayEnvPointers(frames, heap, container) {
  container.clear();

  let currY = 10;

  let h = currY;

  const cache = new Map();

  for (const frame of frames) {
    let maxLen = frame.name.length;
    for (const [key, val] of frame.vals) {
      const length = key.length + (val[0] === "inline" ? val[1].length : 0);
      maxLen = Math.max(maxLen, length);
    }
    maxLen += 5;
    container
      .rect(maxLen * charWidth + 10, charHeight * (frame.vals.length + 1) + 10)
      .dx(15)
      .dy(currY)
      .stroke({ color: "#000000", width: 2 })
      .fill({ color: "#FFFFFF" })
      .radius(10)
      .back();

    container
      .text(frame.name)
      .font("family", "Monaco, monospace")
      .font("size", 14)
      .dx(25)
      .dy(currY);

    currY += charHeight;

    for (const [key, val] of frame.vals) {
      container
        .text(key)
        .font("family", "Monaco, monospace")
        .font("size", 14)
        .dx(35)
        .dy(currY);

      if (val[0] === "ref") {
        const isNewObj = !cache.has(val[1]);
        const isBox = heap[val[1]][0] !== "atomic";
        h = Math.max(h, currY - 5);
        const depth =
          displayElem(
            maxLen * charWidth + 45,
            h + (isBox ? charHeight / 2 : 0),
            val,
            heap,
            container,
            0,
            cache,
            "black",
            maxLen * charWidth + 10,
            currY + 15
          ) + 1;
        if (isNewObj) {
          if (isBox) {
            h += depth * (minWidth + 15);
          } else {
            h += charHeight + 10;
          }
        }
      } else {
        container
          .text(val[1])
          .font("family", "Monaco, monospace")
          .font("size", 14)
          .dx((maxLen - val[1].length) * charWidth + 10)
          .dy(currY);
      }
      currY += charHeight;
    }
    currY += 20;
  }
}

function evaluateFrames(index, frames) {
  const out = [];
  for (const frame of frames) {
    const outFrame = {
      name: frame.name,
      vals: [],
    };
    for (const [key, vals] of frame.vals) {
      let mostRecentVal = null;
      for (const [time, val] of vals) {
        if (time > index) {
          break;
        }
        mostRecentVal = val;
      }
      if (mostRecentVal !== null) {
        outFrame.vals.push([key, mostRecentVal]);
      }
    }
    if (outFrame.vals.length > 0) {
      out.push(outFrame);
    }
  }
  return out;
}

function evaluateObjects(index, objects) {
  const out = {};
  for (const id of Object.keys(objects)) {
    const objType = objects[id][0];
    const objProps = [];
    for (const prop of objects[id][1]) {
      let mostRecentVal = null;
      for (const [time, val] of prop) {
        if (time > index) {
          break;
        }
        mostRecentVal = val;
      }
      if (mostRecentVal !== null) {
        objProps.push(mostRecentVal);
      }
    }
    if (objProps.length === 1) {
      out[id] = [objType, objProps[0]];
    } else {
      out[id] = [objType, objProps];
    }
  }
  return out;
}

export default class SchemeEnvs extends React.Component {
  constructor(props) {
    super(props);
    this.svgRef = React.createRef();
  }

  componentDidMount() {
    this.postRender(null);
  }

  componentDidUpdate(prevProps, prevState, snapshot) {
    this.postRender(snapshot);
  }

  getSnapshotBeforeUpdate() {
    const out = {
      zoom: svgPanZoom(this.svgRef.current).getZoom(),
      pan: svgPanZoom(this.svgRef.current).getPan(),
    };
    svgPanZoom(this.svgRef.current).destroy();
    return out;
  }

  async draw(rawSVG, snapshot) {
    const svg = SVG.adopt(rawSVG).size(3000, 2000);
    svg.clear();

    const evaluatedFrames = evaluateFrames(this.props.index, this.props.frames);
    const evaluatedObjects = evaluateObjects(
      this.props.index,
      this.props.objects
    );
    console.log(evaluatedFrames, evaluatedObjects);

    await displayEnvPointers(evaluatedFrames, evaluatedObjects, svg);

    svgPanZoom(rawSVG, {
      fit: false,
      zoomEnabled: true,
      center: false,
      controlIconsEnabled: true,
    });

    if (snapshot) {
      svgPanZoom(rawSVG).zoom(snapshot.zoom);
      svgPanZoom(rawSVG).pan(snapshot.pan);
    }
  }

  postRender(snapshot) {
    // noinspection JSIgnoredPromiseFromCall
    this.draw(this.svgRef.current, snapshot);
  }

  render() {
    return (
      <div className="scmTree">
        <svg ref={this.svgRef} />
      </div>
    );
  }
}
