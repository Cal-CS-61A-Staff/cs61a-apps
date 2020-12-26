import React from "react";

export default function FolderIndicator(props) {
  return (
    props.folderName && (
      <span className="folderIndicator pathIndicatorElem">
        {" "}
        {props.folderName} <i className="fas fa-chevron-right" />
      </span>
    )
  );
}
