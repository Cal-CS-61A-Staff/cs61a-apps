import React, { useRef, useState } from "react";
import path from "path-browserify";

import FileNameField from "./FileNameField.js";
import ModalButton from "./ModalButton.js";
import { dialogWrap } from "../utils/dialogWrap.js";
import FileTree from "./FileTree.js";
import { FILE } from "../../common/fileTypes.js";

function SaveDialog({ defaultValue, onPathSelect, onDownloadClick }) {
  const [targetFolder, setTargetFolder] = useState("/home");

  const fileNameInputRef = useRef();

  const handleFileSelect = (file) => {
    if (file.type === FILE) {
      setTargetFolder(path.dirname(file.location));
      fileNameInputRef.current.setText(path.basename(file.location));
    } else {
      setTargetFolder(file.location);
    }
  };

  const handleSubmit = (name) => {
    onPathSelect(path.join(targetFolder, name));
  };

  return (
    <>
      <FileNameField
        defaultValue={defaultValue}
        ref={fileNameInputRef}
        onClick={handleSubmit}
      />
      <div className="directoryIndicator">In directory: {targetFolder}</div>
      <FileTree onFileSelect={handleFileSelect} />
      <ModalButton buttonText="Download" onClick={onDownloadClick}>
        <p>Or download a copy of your code to save on your computer.</p>
      </ModalButton>
    </>
  );
}

export default dialogWrap("Save", SaveDialog, "column");
