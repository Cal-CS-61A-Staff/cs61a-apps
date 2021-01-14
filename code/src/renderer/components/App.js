/* eslint-disable import/first,global-require */
let hot;
if (!ELECTRON) {
  ({ hot } = require("react-hot-loader/root"));
}
import * as React from "react";

import LaunchScreen from "./LaunchScreen.js";
import MainScreen from "./MainScreen.js";

let MenuBar;
if (!ELECTRON) {
  MenuBar = require("./MenuBar.js").default;
}
import { sendNoInteract } from "../utils/communication.js";
import { OPEN_FILE } from "../../common/communicationEnums.js";

class App extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      launch: true,
      initFile: null,
    };
  }

  componentDidMount() {
    if (this.props.path) {
      sendNoInteract({
        type: OPEN_FILE,
        location: this.props.path,
      }).then((value) => {
        if (value.success) {
          this.handleFileCreate(value.file);
        }
      });
    }

    window.history.replaceState(false, "", "/");

    if (!ELECTRON && window.initData) {
      const { loadFile, srcOrigin, startInterpreter } = initData;

      if (loadFile) {
        this.handleFileCreate(
          {
            name: loadFile.fileName,
            location: null,
            content: loadFile.data,
            shareRef: loadFile.shareRef,
          },
          startInterpreter,
          srcOrigin
        );
      }
    }
  }

  handleAllClosed = () => {
    this.setState({ launch: true });
  };

  handleFileCreate = (file, startInterpreter, srcOrigin) => {
    this.setState({
      launch: false,
      initFile: file,
      startInterpreter,
      srcOrigin,
    });
  };

  render() {
    let primaryElem;
    if (this.state.launch) {
      primaryElem = <LaunchScreen onFileCreate={this.handleFileCreate} />;
    } else {
      primaryElem = (
        <MainScreen
          onAllClosed={this.handleAllClosed}
          initFile={this.state.initFile}
          srcOrigin={this.state.srcOrigin}
          startInterpreter={this.state.startInterpreter}
        />
      );
    }

    if (ELECTRON) {
      return primaryElem;
    } else {
      console.log(this.state);
      return (
        <>
          <MenuBar />
          {primaryElem}
        </>
      );
    }
  }
}

export default ELECTRON ? App : hot(App);
