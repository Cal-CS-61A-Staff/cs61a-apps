import React, { Component } from "react";
import * as ReactDOM from "react-dom";

export function dialogWrap(name, Contents, flexDirection) {
  return class extends Component {
    handleClick = (e) => {
      if (e.target === e.currentTarget) {
        this.props.onClose();
      }
    };

    render() {
      return (
        <div className="modal" onClick={this.handleClick}>
          <div className="modalBody">
            <span className="close" onClick={this.props.onClose}>
              &times;
            </span>
            <div className="modalHeader">{this.props.title || name}</div>
            <div className="modalContent" style={{ flexDirection }}>
              <Contents {...this.props} />
            </div>
          </div>
        </div>
      );
    }
  };
}

export function loadDialog(Dialog, props) {
  const elem = document.getElementById("modalOverlay");
  const { onClose, ...rest } = props;

  function handleClose() {
    ReactDOM.unmountComponentAtNode(elem);
    onClose();
  }

  ReactDOM.render(<Dialog onClose={handleClose} {...rest} />, elem);
}

export function closeDialog() {
  const elem = document.getElementById("modalOverlay");
  ReactDOM.unmountComponentAtNode(elem);
}
