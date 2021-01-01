/* eslint-disable react/no-array-index-key */
import * as React from "react";
import $ from "jquery";

import RunStopButton from "./RunStopButton";
import StdinElem from "./StdinElem";
import OutputElem from "./OutputElem";
import glWrap from "../utils/glWrap";

import "highlight.js/styles/darcula.css";

class Output extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      history: [""],
      historyIndex: 0,
    };
    this.inputRef = React.createRef();
    this.outputRef = React.createRef();
  }

  componentDidMount() {
    this.postRender();
  }

  componentDidUpdate() {
    this.postRender();
  }

  componentWillUnmount() {
    this.props.onStop();
  }

  handleOutputClick = () => {
    if (this.inputRef.current) {
      setTimeout(() => {
        if (
          window.getSelection().rangeCount === 0 ||
          window.getSelection().getRangeAt(0).collapsed
        ) {
          this.inputRef.current.focus();
        }
      }, 0);
    }
  };

  handleInput = (text) => {
    this.postRender(text);
    this.props.onInput(text);
    this.setState((state) => {
      const newHistory = state.history
        .slice(0, state.history.length - 1)
        .concat([...text.trimEnd().split("\n"), ""]);
      return {
        history: newHistory,
        historyIndex: newHistory.length - 1,
      };
    });
  };

  handleKeyDown = (e) => {
    if (e.keyCode === 38) {
      e.preventDefault();
      this.setState((state) => {
        const newIndex = Math.max(0, state.historyIndex - 1);
        this.inputRef.current.setText(state.history[newIndex]);
        return {
          historyIndex: newIndex,
        };
      });
    } else if (e.keyCode === 40) {
      e.preventDefault();
      this.setState((state) => {
        const newIndex = Math.min(
          state.history.length - 1,
          state.historyIndex + 1
        );
        this.inputRef.current.setText(state.history[newIndex]);
        return {
          historyIndex: newIndex,
        };
      });
    }
  };

  postRender() {
    this.outputRef.current.scrollTop = this.outputRef.current.scrollHeight;
    $(document.body).hide().show(0);
  }

  render() {
    return (
      <>
        <div className="outputControls">
          <RunStopButton
            codeRunning={this.props.outputActive}
            onStop={this.props.onStop}
            onRestart={this.props.onRestart}
          />
        </div>
        <div
          className="outputWrapper"
          ref={this.outputRef}
          onClick={this.handleOutputClick}
          onKeyDown={this.handleKeyDown}
        >
          <div className="output">
            {this.props.data.map((elem, index) => (
              <OutputElem key={index} lang={this.props.lang} {...elem} />
            ))}
            {this.props.outputActive && (
              <StdinElem
                ref={this.inputRef}
                onInput={this.handleInput}
                lang={this.props.lang}
              />
            )}
            <div className="outputScrollAnchor" />
          </div>
        </div>
      </>
    );
  }
}

export default glWrap(Output, "bottom", 30, "output", [
  "output",
  "okResults",
  "terminal",
]);
