import React from "react";
import Output from "./Output.js";
import startConsole from "../utils/console.js";
import { CONSOLE_EDIT } from "../../common/communicationEnums.js";
import { INPUT, ERROR, OUTPUT } from "../../common/outputTypes.js";

export default class Console extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      outputData: [],
      outputActive: false,

      interactCallback: null,
      killCallback: null,
      detachCallback: null,
    };
    this.outputRef = React.createRef();
  }

  componentDidMount() {
    this.outputRef.current.forceOpen();
    this.run();
  }

  run = () => {
    if (this.state.killCallback) {
      this.state.detachCallback();
      this.state.killCallback();
    }

    const [interactCallback, killCallback, detachCallback] = startConsole(
      (out) => this.handleOutputUpdate(out, false),
      (out) => this.handleOutputUpdate(out, true),
      this.handleHalt
    );

    const numTrunc = this.state.outputData.length;

    this.setState((state) => ({
      interactCallback,
      killCallback,
      detachCallback,
      outputData: state.outputData.slice(numTrunc),
      outputActive: true,
    }));
  };

  handleOutputUpdate = (text, isErr) => {
    if (text.cmd) {
      if (text.cmd === CONSOLE_EDIT) {
        this.props.onLoadFile(text.data.file, text.data.startInterpreter);
      }
    } else {
      this.setState((state) => {
        const outputData = state.outputData.concat([
          {
            text,
            type: isErr ? ERROR : OUTPUT,
          },
        ]);
        return { outputData };
      });
    }
  };

  handleHalt = (text) => {
    this.handleOutputUpdate(text, true);
    this.setState({ outputActive: false });
  };

  handleStop = () => {
    this.state.killCallback();
  };

  handleInput = (line) => {
    this.state.interactCallback(line);
    this.setState((state) => {
      const outputData = state.outputData.concat([
        {
          text: line,
          type: INPUT,
        },
      ]);
      return { outputData };
    });
  };

  render() {
    return (
      <Output
        ref={this.outputRef}
        title={`Console (${this.props.i + 1})`}
        data={this.state.outputData}
        lang="bash"
        outputActive={this.state.outputActive}
        onStop={this.handleStop}
        onRestart={this.run}
        onInput={this.handleInput}
      />
    );
  }
}
