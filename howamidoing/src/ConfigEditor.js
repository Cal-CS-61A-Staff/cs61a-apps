import React, { useState } from "react";
import $ from "jquery";

import AceEditor from "react-ace";

import "ace-builds/src-noconflict/mode-javascript";
import "ace-builds/src-noconflict/theme-github";

var original = "";

$.ajax("/config/config.js", { async: false, dataType: "text" }).done(
  (origConfig) => {
    original = origConfig;
  }
);

export default function ConfigEditor() {
  const editorRef = React.useRef();
  const [modified, setModified] = useState(false);
  const [saving, setSaving] = useState(false);

  const updateModified = () => {
    const curr = editorRef.current.editor.getValue();
    setModified(curr !== original);
  };

  const postConfig = () => {
    setSaving(true);

    const newOrig = editorRef.current.editor.getValue().slice();

    $.post("/setConfig", { data: newOrig, dataType: "text" }).done(() => {
      setSaving(false);

      original = newOrig;
      updateModified();
    });
  };

  return (
    <>
      <AceEditor
        mode="javascript"
        theme="github"
        ref={editorRef}
        defaultValue={original.slice()}
        name="configEditor"
        onChange={updateModified}
        style={{
          width: "100%",
        }}
        showPrintMargin={false}
        wrapEnabled={true}
      />
      <button
        type="submit"
        className="btn btn-primary"
        style={{
          marginTop: "10px",
          marginBottom: "10px",
        }}
        onClick={(e) => {
          e.preventDefault();
          postConfig();
        }}
        id="saveButton"
        disabled={saving || !modified}
      >
        {saving ? "Saving..." : modified ? "Save Configuration" : "No Changes"}
      </button>
    </>
  );
}
