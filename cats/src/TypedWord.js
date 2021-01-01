import React from "react";
import "./TypedWord.css";

export default class TypedWord extends React.PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      updated: false,
    };
  }

  componentDidUpdate() {
    if (!this.state.updated) {
      // eslint-disable-next-line react/no-did-update-set-state
      this.setState({ updated: true });
    }
  }

  render() {
    let className = "TypedWord ";
    if (this.state.updated && this.props.incorrect) {
      className += "both";
    } else if (this.props.incorrect) {
      className += "incorrect";
    } else if (this.state.updated) {
      className += "updated";
    }

    return <span className={className}>{this.props.word} </span>;
  }
}
