import React from "react";
import FolderIndicator from "./FolderIndicator";
import FileIndicator from "./FileIndicator";

export default function PathIndicator(props) {
  const folderPath = props.path.slice(0, props.path.length - 1);
  const fileName = props.path[props.path.length - 1];
  const folderElems = folderPath.map(
    // eslint-disable-next-line react/no-array-index-key
    (elem, index) => <FolderIndicator key={index} folderName={elem} />
  );
  return (
    <span className="pathIndicator">
      {folderElems}
      <FileIndicator fileName={fileName} />
    </span>
  );
}
