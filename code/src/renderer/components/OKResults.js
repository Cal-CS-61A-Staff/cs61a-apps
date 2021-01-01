import React from "react";
import GoldenLayout from "imports-loader?$=jquery!golden-layout";
import $ from "jquery";
import ReactDOM from "react-dom";
import glWrap from "../utils/glWrap";
import TestDetails from "./TestDetails";
import TestList from "./TestList";

class OKResults extends React.Component {
  static getActiveTest(props) {
    for (const elem of props.data) {
      if (!elem.success) {
        return {
          selectedProblem: elem.name[0],
          selectedTest: elem,
        };
      }
    }
    return { selectedProblem: null, selectedTest: null };
  }

  constructor(props) {
    super(props);
    this.divRef = React.createRef();
    this.state = {
      testList: null,
      testDetails: null,
      ...OKResults.getActiveTest(props),
    };
  }

  componentDidMount() {
    let testList;
    let testDetails;

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
                  testList = comp;
                },
              },
              width: 25,
            },
            {
              type: "component",
              componentName: "dummyComponent",
              componentState: {
                callback: (comp) => {
                  testDetails = comp;
                },
              },
              width: 75,
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
      testList,
      testDetails,
    });
  }

  handleProblemClick = (selectedProblem) => {
    this.setState({
      selectedProblem,
      selectedTest: null,
    });
  };

  handleTestClick = (selectedTest) => {
    this.setState({ selectedTest });
  };

  // eslint-disable-next-line camelcase
  UNSAFE_componentWillReceiveProps(nextProps) {
    if (this.props.data !== nextProps.data) {
      this.setState(OKResults.getActiveTest(nextProps));
    }
  }

  render() {
    let rest = false;
    if (this.state.testList) {
      const selectedProblemData = {
        rawName: this.state.selectedProblem,
        raw: [""],
        success: true,
      };
      for (const elem of this.props.data) {
        if (elem.name[0] === this.state.selectedProblem) {
          selectedProblemData.raw.push(elem.raw);
          selectedProblemData.success =
            selectedProblemData.success && elem.success;
        }
      }
      selectedProblemData.raw = selectedProblemData.raw.join(
        `\n${"-".repeat(69)}\n`
      );

      rest = (
        <>
          {ReactDOM.createPortal(
            <TestList
              data={this.props.data}
              indentLevel={0}
              onProblemClick={this.handleProblemClick}
              onTestClick={this.handleTestClick}
              selectedProblem={this.state.selectedProblem}
              selectedTest={this.state.selectedTest}
            />,
            this.state.testList.getElement().get(0)
          )}
          {ReactDOM.createPortal(
            <TestDetails
              active={this.state.active}
              data={this.state.selectedTest || selectedProblemData}
              onDebug={this.props.onDebug}
            />,
            this.state.testDetails.getElement().get(0)
          )}
        </>
      );
    }
    return (
      <>
        <div ref={this.divRef} className="okResults" />
        {rest}
      </>
    );
  }
}

export default glWrap(OKResults, "bottom", 30, "okResults", [
  "okResults",
  "output",
  "terminal",
]);
