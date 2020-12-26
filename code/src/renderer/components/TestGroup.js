import React from "react";
import SuccessIcon from "./SuccessIcon";
import TestElem from "./TestElem";

export default class TestGroup extends React.Component {
  handleClick = () => {
    this.props.onProblemClick(this.props.name);
  };

  render() {
    let children = null;

    const expanded = this.props.name === this.props.selectedProblem;

    if (expanded) {
      children = this.props.children.map((child) => (
        <TestElem
          key={child.rawName}
          name={child.name.slice(1).join(" > ")}
          onClick={() => this.props.onTestClick(child)}
          highlight={child === this.props.selectedTest}
          success={child.success}
        />
      ));
    }

    let success = true;
    for (const child of this.props.children) {
      success = success && child.success;
    }

    const successDisplay = <SuccessIcon success={success} />;
    const expandIconClass = expanded
      ? "fas fa-caret-down"
      : "fas fa-caret-right";

    return (
      <>
        <div
          className="testListItem"
          onClick={this.handleClick}
          style={{
            paddingLeft: 10,
            ...(expanded ? { background: "slategray" } : {}),
          }}
        >
          {" "}
          <i className={expandIconClass} />
          {"  "}
          {expanded ? false : successDisplay} {this.props.name}
        </div>
        {children}
      </>
    );
  }
}
