import * as React from "react";
import $ from "jquery";
import GoldenLayout from "golden-layout";
import ReactDOM from "react-dom";
import glWrap from "../../../renderer/utils/glWrap.js";
import SchemeTree from "./SchemeTree.js";
import SchemeEnvs from "./SchemeEnvs.js";
import PositionChooser from "../../../renderer/components/PositionChooser.js";

import "./SchemeDebugger.css";

class SchemeDebugger extends React.PureComponent {
  constructor(props) {
    super(props);
    this.divRef = React.createRef();
    this.state = {
      treeView: null,
      envView: null,
      index: 1,
    };
  }

  componentDidMount() {
    let treeView;
    let envView;

    const config = {
      settings: { hasHeaders: false },
      content: [
        {
          type: "row",
          content: [
            {
              type: "component",
              componentName: "dummyComponent",
              componentState: {
                callback: (comp) => {
                  treeView = comp;
                },
              },
              width: 50,
            },
            {
              type: "component",
              componentName: "dummyComponent",
              componentState: {
                callback: (comp) => {
                  envView = comp;
                },
              },
              width: 50,
            },
          ],
        },
      ],
    };

    const elem = $(this.divRef.current);

    const layout = new GoldenLayout(config, elem);
    // eslint-disable-next-line
    layout.registerComponent("dummyComponent", function (container, state) {
      state.callback(container);
    });

    this.props.glContainer.on("resize", () => {
      layout.updateSize(elem.width(), elem.height());
    });

    layout.init();

    // noinspection JSUnusedAssignment
    this.setState({
      treeView,
      envView,
    });
  }

  handleChange = (index) => {
    this.setState({ index: index + 1 });
  };

  // eslint-disable-next-line camelcase
  UNSAFE_componentWillReceiveProps(nextProps) {
    if (this.props.data !== nextProps.data) {
      this.setState({ index: 1 });
    }
  }

  render() {
    let rest = false;
    if (this.state.treeView) {
      rest = (
        <>
          {ReactDOM.createPortal(
            <SchemeTree
              data={this.props.data.roots}
              index={this.state.index}
            />,
            this.state.treeView.getElement().get(0)
          )}
          {ReactDOM.createPortal(
            <SchemeEnvs
              frames={this.props.data.frames}
              objects={this.props.data.objects}
              index={this.state.index}
            />,
            this.state.envView.getElement().get(0)
          )}
        </>
      );
    }
    return (
      <>
        <PositionChooser
          num={this.props.data.endTime - 1}
          value={this.state.index - 1}
          onChange={this.handleChange}
        />
        <div ref={this.divRef} className="scmDebug" />
        {rest}
      </>
    );
  }
}

export default glWrap(SchemeDebugger, "right", 50, "debugger", [
  "editor",
  "debugger",
]);
