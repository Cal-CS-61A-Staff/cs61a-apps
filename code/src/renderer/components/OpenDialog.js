import * as React from "react";
import UploadFileSelector from "./UploadFileSelector.js";
import { dialogWrap } from "../utils/dialogWrap.js";
import TreeFileSelector from "./TreeFileSelector.js";

function OpenDialog({ onFileSelect }) {
  return (
    <>
      <TreeFileSelector onFileSelect={onFileSelect} />
      <UploadFileSelector onFileSelect={onFileSelect} />
    </>
  );
}

export default dialogWrap("Open", OpenDialog, "row");
