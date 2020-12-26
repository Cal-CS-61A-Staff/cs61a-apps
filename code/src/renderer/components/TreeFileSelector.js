import React from "react";
import FileTree from "./FileTree.js";
import { FILE } from "../../common/fileTypes.js";

export default function TreeFileSelector({ onFileSelect }) {
  const handleFileSelect = (file) => {
    if (file.type === FILE) {
      onFileSelect(file);
    }
  };

  return (
    <div className="modalCol">
      <div className="TreeFileSelector">
        <span className="browserFileSelector">Select Files</span>
        <FileTree onFileSelect={handleFileSelect} />
      </div>
    </div>
  );
}
