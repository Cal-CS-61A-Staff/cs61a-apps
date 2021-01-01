import * as React from "react";
import SVG from "svg.js";
import { displayElem, displayTree } from "../utils/diagramming.js";

export default class OutputDrawElem extends React.PureComponent {
  constructor(props) {
    super(props);
    this.svgRef = React.createRef();
  }

  componentDidMount() {
    this.draw(this.svgRef.current);
  }

  draw(rawSVG) {
    const svg = SVG(rawSVG);
    svg.clear();
    const [id, allData] = this.props.data;
    if (id === "Tree") {
      displayTree(allData, svg);
    } else {
      displayElem(0, 14, id, allData, svg, 0, new Map(), "white");
    }

    rawSVG.setAttribute("height", svg.bbox().h + 23);
  }

  render() {
    return (
      <div>
        <svg ref={this.svgRef} style={{ width: "100%" }} />
      </div>
    );
  }
}
