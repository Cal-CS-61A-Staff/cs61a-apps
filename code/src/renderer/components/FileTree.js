import React, { useEffect, useState } from "react";
import TreeView from "@material-ui/lab/TreeView";
import TreeItem from "@material-ui/lab/TreeItem";
import { createMuiTheme } from "@material-ui/core";
import { ThemeProvider } from "@material-ui/styles";
import Collapse from "@material-ui/core/Collapse";

import { useAsync } from "../utils/hooks.js";
import { sendNoInteract } from "../utils/communication.js";
import { OPEN_FILE } from "../../common/communicationEnums.js";
import { DIRECTORY } from "../../common/fileTypes.js";
import { useAuthData } from "../utils/okUtils.js";
import { login } from "../utils/auth.js";

const LOCKED = "LOCKED";

const theme = createMuiTheme({
  transitions: { create: () => "none" },
});

const NoCollapse = React.forwardRef((props, ref) => (
  <Collapse {...props} timeout={0} ref={ref} />
));

export default function FileTree({ onFileSelect }) {
  const [expanded, setExpanded] = React.useState(["Element-/"]);

  const handleToggle = (nodeID, isExpanding) => {
    if (isExpanding) {
      setExpanded((currExpanded) => [
        ...new Set(currExpanded.concat([nodeID])),
      ]);
    } else {
      setExpanded((currExpanded) => currExpanded.filter((x) => x !== nodeID));
    }
  };

  return (
    <div className="FileTree">
      <ThemeProvider theme={theme}>
        <TreeView
          defaultCollapseIcon={<i className="fas fa-folder-open" />}
          defaultExpandIcon={<i className="fas fa-folder" />}
          defaultEndIcon={<i className="fas fa-file-code" />}
          expanded={expanded}
        >
          <TreeElement
            location="/"
            onToggle={handleToggle}
            onFileSelect={onFileSelect}
          />
        </TreeView>
      </ThemeProvider>
    </div>
  );
}

function TreeElement({ location, onToggle, onFileSelect }) {
  const [expanded, _setExpanded] = useState(location === "/");
  const [fileType, setFileType] = useState(null);

  const { loggedOut } = useAuthData();

  const [fileClicked, setFileClicked] = useState(false);

  const nodeID = `Element-${location}`;

  const setExpanded = (x) => {
    _setExpanded(x);
    onToggle(nodeID, x);
  };

  useEffect(() => () => onToggle(nodeID, false), []);

  const { success, file } = useAsync(
    () =>
      expanded || fileClicked || fileType
        ? sendNoInteract({ type: OPEN_FILE, location })
        : {},
    {},
    [!!(expanded || fileClicked || fileType), location, loggedOut]
  );

  if (success === false && !fileType) {
    setFileType(LOCKED);
    login();
  }

  const name = location === "/" ? location : location.split("/").pop();
  const isDirectory =
    fileType === DIRECTORY || (!fileType && !name.includes("."));

  let children = <TreeItem nodeId="test" label="Loading..." />;
  if (expanded && success && file.type === DIRECTORY) {
    children = file.content.map((x) => (
      <TreeElement
        key={x}
        onToggle={onToggle}
        location={x}
        onFileSelect={onFileSelect}
      />
    ));
  }

  if (success && !fileType) {
    setFileType(file.type);
  }

  if (expanded && !isDirectory) {
    setExpanded(false);
  }

  const handleClick = () => {
    if (expanded) {
      setExpanded(false);
    } else if (!expanded && isDirectory) {
      setExpanded(true);
    }
    if (fileType === LOCKED) {
      login();
    } else if (fileType && fileType !== LOCKED) {
      onFileSelect(file);
    } else if (fileType !== LOCKED) {
      setFileClicked(true);
    }
  };

  if (fileClicked && fileType && fileType !== LOCKED) {
    onFileSelect(file);
    setFileClicked(false);
  }

  let icon;
  if (expanded) {
    icon = <i className="fas fa-folder-open" />;
  } else if (isDirectory) {
    icon = <i className="fas fa-folder" />;
  } else if (fileType === LOCKED) {
    icon = <i className="fas fa-lock" />;
  } else {
    icon = <i className="fas fa-file-code" />;
  }

  return (
    <TreeItem
      nodeId={nodeID}
      label={name}
      icon={icon}
      onClick={handleClick}
      TransitionComponent={NoCollapse}
    >
      {children}
    </TreeItem>
  );
}
