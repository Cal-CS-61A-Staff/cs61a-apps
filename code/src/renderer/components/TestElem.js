import React from "react";
import SuccessIcon from "./SuccessIcon";

export default class TestElem extends React.Component {
  constructor(props) {
    super(props);
    this.divRef = React.createRef();
  }

  componentDidMount() {
    this.divRef.current.scrollIntoViewIfNeeded();
  }

  handleClick = () => {
    this.props.onClick();
  };

  render() {
    return (
      <div
        ref={this.divRef}
        className="testElem testListItem"
        onClick={this.handleClick}
        style={this.props.highlight ? { background: "darkslategrey" } : {}}
      >
        <SuccessIcon success={this.props.success} /> {this.props.name}
      </div>
    );
  }
}
