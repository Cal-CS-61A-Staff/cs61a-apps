import * as React from "react";
import * as ReactDOM from "react-dom";
import { checkAllClosed, requestContainer } from "./goldenLayout";

export default function glWrap(Component, position, targetDim, type, friends) {
  function getGlContainer() {
    return requestContainer(position, targetDim, type, friends);
  }

  return class extends React.Component {
    constructor(props) {
      super(props);
      this.state = {
        glContainer: null,
      };
    }

    componentWillUnmount() {
      if (this.state.glContainer) {
        this.state.glContainer.unbind("destroy");
        this.state.glContainer.close();
      }
    }

    forceOpen() {
      if (this.state.glContainer) {
        this.state.glContainer.parent.parent.setActiveContentItem(
          this.state.glContainer.parent
        );
        return;
      }
      const container = getGlContainer();
      container.on("destroy", () => {
        this.setState(
          {
            glContainer: null,
          },
          checkAllClosed
        );
      });

      this.setState({
        glContainer: container,
      });
    }

    render() {
      if (!this.state.glContainer) {
        return null;
      }
      this.state.glContainer.setTitle(this.props.title);
      return ReactDOM.createPortal(
        <Component glContainer={this.state.glContainer} {...this.props} />,
        this.state.glContainer.getElement().get(0)
      );
    }
  };
}
