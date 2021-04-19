import * as React from "react";
import * as hljs from "highlight.js";
import { LARK } from "../../common/languages";
import {
  getCurrentCursorPosition,
  setCurrentCursorPosition,
} from "../utils/cursorPositioning.js";

export default class StdinElem extends React.Component {
  constructor(props) {
    super(props);
    this.inputRef = React.createRef();
  }

  componentDidMount() {
    this.postRender();
  }

  componentDidUpdate() {
    this.postRender();
  }

  setText(text) {
    this.inputRef.current.innerText = text;
    setCurrentCursorPosition(
      this.inputRef.current,
      this.inputRef.current.innerText.length
    );
  }

  handleKeyDown = (e) => {
    if (e.keyCode === 9) {
      e.preventDefault();
      document.execCommand("insertHTML", false, "    ");
    } else if (e.keyCode === 13) {
      e.preventDefault();
      this.props.onInput(`${this.inputRef.current.innerText}\n`);
      this.setText("");
    }
  };

  handleInput = (e) => {
    let text = e.currentTarget.innerText;
    const lines = text.split(/\r\n|\r|\n/);
    if (lines.length > 1) {
      this.props.onInput(`${lines.slice(0, lines.length - 1).join("\n")}\n`);
    }
    text = lines[lines.length - 1];
    if (lines.length > 1) {
      this.setText(text);
    }
    this.postRender();
  };

  postRender() {
    const node = this.inputRef.current;
    const cursorPos = getCurrentCursorPosition(node);
    this.inputRef.current.innerText = node.innerText;
    if (this.props.lang !== LARK) {
      hljs.highlightBlock(node);
    }
    if (cursorPos !== -1) {
      setCurrentCursorPosition(node, cursorPos);
    }
  }

  focus() {
    this.inputRef.current.focus();
    setCurrentCursorPosition(
      this.inputRef.current,
      this.inputRef.current.innerText.length
    );
  }

  render() {
    return (
      <span
        ref={this.inputRef}
        className={`consoleInput lang-${this.props.lang.toLowerCase()}`}
        onInput={this.handleInput}
        onKeyDown={this.handleKeyDown}
        spellCheck={false}
        contentEditable="true"
      />
    );
  }
}
