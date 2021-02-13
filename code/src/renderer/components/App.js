/* eslint-disable import/first,global-require */
let hot;
if (!ELECTRON) {
  ({ hot } = require("react-hot-loader/root"));
}
import { useEffect, useState } from "react";
import * as React from "react";
import useSettings from "../utils/settingsHandler";

import LaunchScreen from "./LaunchScreen.js";
import MainScreen from "./MainScreen.js";

let MenuBar;
if (!ELECTRON) {
  MenuBar = require("./MenuBar.js").default;
}
import { sendNoInteract } from "../utils/communication.js";
import { OPEN_FILE } from "../../common/communicationEnums.js";

const App = ({ path }) => {
  const [launch, setLaunch] = useState(true);
  const [initFile, setInitFile] = useState(null);
  const [startInterpreter, setStartInterpreter] = useState();
  const [srcOrigin, setSrcOrigin] = useState();

  const settings = useSettings();

  const handleAllClosed = () => {
    setLaunch(true);
  };

  const handleFileCreate = (file, interpreter, origin) => {
    setLaunch(false);
    setInitFile(file);
    setStartInterpreter(interpreter);
    setSrcOrigin(origin);
  };

  let primaryElem;
  if (launch) {
    primaryElem = <LaunchScreen onFileCreate={handleFileCreate} />;
  } else {
    primaryElem = (
      <MainScreen
        onAllClosed={handleAllClosed}
        initFile={initFile}
        srcOrigin={srcOrigin}
        startInterpreter={startInterpreter}
        settings={settings}
      />
    );
  }

  useEffect(() => {
    if (path) {
      sendNoInteract({
        type: OPEN_FILE,
        location: path,
      }).then((value) => {
        if (value.success) {
          handleFileCreate(value.file);
        }
      });
    }

    window.history.replaceState(false, "", "/");

    if (!ELECTRON && window.initData) {
      const {
        loadFile,
        srcOrigin: initSrcOrigin,
        startInterpreter: initStartInterpreter,
      } = initData;

      if (loadFile) {
        handleFileCreate(
          {
            name: loadFile.fileName,
            location: null,
            content: loadFile.data,
            shareRef: loadFile.shareRef,
          },
          initSrcOrigin,
          initStartInterpreter
        );
      }
    }
  });

  if (ELECTRON) {
    return primaryElem;
  } else {
    return (
      <>
        <MenuBar />
        {primaryElem}
      </>
    );
  }
};

export default ELECTRON ? App : hot(App);
