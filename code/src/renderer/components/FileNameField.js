import React, { Component } from "react";

export default class FileNameField extends Component {
  constructor(props) {
    super(props);
    this.inputRef = React.createRef();
  }

  componentDidMount() {
    this.inputRef.current.focus();
    this.inputRef.current.select();
  }

  setText = (text) => {
    this.inputRef.current.value = text;
    this.inputRef.current.focus();
    this.inputRef.current.select();
  };

  handleKeyUp = (e) => {
    if (e.keyCode === 13) {
      this.handleClick();
    }
  };

  handleClick = () => {
    this.props.onClick(this.inputRef.current.value);
  };

  render() {
    return (
      <div>
        <p>Enter file name to save your work in the browser:</p>
        <input
          ref={this.inputRef}
          className="fileNameField"
          defaultValue={this.props.defaultValue}
          spellCheck={false}
          onKeyUp={this.handleKeyUp}
        />
        <button
          className="fileNameSubmitBtn"
          type="button"
          onClick={this.handleClick}
        >
          Save
        </button>
      </div>
    );
  }
}
