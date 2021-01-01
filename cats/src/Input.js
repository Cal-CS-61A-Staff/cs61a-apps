import React, { Component } from "react";
import "./Input.css";
import TypedWord from "./TypedWord.js";

export default class Input extends Component {
  constructor(props) {
    super(props);
    this.inputRef = React.createRef();
  }

  componentDidMount() {
    if (this.inputRef.current) {
      this.inputRef.current.focus();
    }
  }

  handleClick = () => {
    if (this.inputRef.current) {
      this.inputRef.current.focus();
    }
  };

  render() {
    const typedWords = this.props.words.map((word, index) => {
      const incorrect = this.props.correctWords[index] !== word;
      return <TypedWord key={index} word={word} incorrect={incorrect} />;
    });
    return (
      <div className="Input">
        And type them below:
        <div className="InputBox" onClick={this.handleClick}>
          {typedWords}
          {this.props.active && (
            <InputField
              ref={this.inputRef}
              active={this.props.active}
              onChange={this.props.onChange}
              onWordTyped={this.props.onWordTyped}
              popPrevWord={this.props.popPrevWord}
            />
          )}
        </div>
      </div>
    );
  }
}

class InputField extends Component {
  constructor(props) {
    super(props);
    this.inputRef = React.createRef();
  }

  handleKeyDown = (e) => {
    if (e.keyCode !== 8) {
      return;
    }
    if (e.target.innerText !== "") {
      return;
    }
    this.setText(this.props.popPrevWord(), false);
    e.preventDefault();
    this.handleInput(e);
  };

  handleInput = (e) => {
    const value = e.target.innerText;
    if (/\s/.test(value)) {
      const words = value.split(/\s/);
      const newWords = [];
      for (let i = 0; i !== words.length - 1; ++i) {
        const ok = this.props.onWordTyped(words[i]);
        if (!ok) {
          newWords.push(words[i]);
        }
      }
      this.setText(newWords.join(" ") + words[words.length - 1]);
    } else {
      this.props.onChange(value);
    }
  };

  setText = (text, toStart) => {
    this.inputRef.current.innerText = text;

    // https://stackoverflow.com/questions/1125292/how-to-move-cursor-to-end-of-contenteditable-entity/3866442#3866442
    const range = document.createRange();
    range.selectNodeContents(this.inputRef.current);
    range.collapse(toStart);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  };

  focus() {
    this.inputRef.current.focus();
  }

  render() {
    return (
      <span
        className="InputField"
        ref={this.inputRef}
        contentEditable={this.props.active}
        onInput={this.handleInput}
        onKeyDown={this.handleKeyDown}
        onPaste={(e) => e.preventDefault()}
      />
    );
  }
}
