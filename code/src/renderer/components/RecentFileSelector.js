import React from "react";
import CardList from "./CardList.js";

export default function RecentFileSelector({ files, onFileSelect }) {
  return (
    <CardList
      header={files.length ? "Recent Local Files" : "No recent local files."}
      items={files.slice(0, 3).map((x) => x.name)}
      onClick={(i) => onFileSelect(files[i])}
    />
  );
}
