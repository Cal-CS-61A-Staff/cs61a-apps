import * as React from "react";
import SVG from "svg.js";
import svgPanZoom from "svg-pan-zoom/dist/svg-pan-zoom.min.js";

export default class SVGCanvas extends React.Component {
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

    await this.props.draw(svg);

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
      <div className="canvas">
        <svg ref={this.svgRef} />
      </div>
    );
  }
}
