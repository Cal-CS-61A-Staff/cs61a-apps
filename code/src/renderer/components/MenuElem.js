import React, { Component } from "react";
import Mousetrap from "mousetrap";
import "mousetrap-global-bind";
import { sendMenuEvent } from "../../web/webMenuHandler.js";

export default class MenuElem extends Component {
  componentDidMount() {
    Mousetrap.bindGlobal(this.props.shortcut, this.handleClick);
  }

  componentWillUnmount() {
    Mousetrap.unbind(this.props.shortcut);
  }

  handleClick = () => {
    sendMenuEvent(this.props.code);
    return false;
  };

  render() {
    return (
      <div onClick={this.handleClick} className="menuElem">
        {this.props.name}
      </div>
    );
  }
}
