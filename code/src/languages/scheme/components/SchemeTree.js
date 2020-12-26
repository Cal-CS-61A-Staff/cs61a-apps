import * as React from "react";
import $ from "jquery";
import svgPanZoom from "svg-pan-zoom/dist/svg-pan-zoom.min.js";
import SVG from "svg.js";

const UNEVALUATED = 0;
const EVALUATING = 1;
const APPLYING = 2;
const EVALUATED = 3;

function getDims() {
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

const charHeight = getDims()[1];
const charWidth = getDims()[0];

export default class SchemeTree extends React.PureComponent {
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

  getDataAtIndex(data, i) {
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
      out.children.push(this.getDataAtIndex(child, i));
    }

    return out;
  }

  displayTreeWorker(data, container, x, y, level, starts) {
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
      this.displayTreeWorker(
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

  async displayTree(svg, allData) {
    let currData;
    for (const data of allData) {
      if (data[0] > this.props.index) {
        break;
      }
      [, currData] = data;
    }
    const data = this.getDataAtIndex(currData, this.props.index);

    // svg.clear();

    this.displayTreeWorker(data, svg, 10, 15, 0, [0]);
  }

  async draw(rawSVG, snapshot) {
    const svg = SVG.adopt(rawSVG).size(3000, 2000);
    svg.clear();

    await this.displayTree(svg, this.props.data);

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
