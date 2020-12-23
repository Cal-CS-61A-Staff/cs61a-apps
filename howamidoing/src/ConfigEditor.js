import React from "react";
import $ from "jquery";

import AceEditor from "react-ace";

import "ace-builds/src-noconflict/mode-javascript";
import "ace-builds/src-noconflict/theme-github";

export default function ConfigEditor() {
  var config = "";

  const setConfig = (newConfig) => (config = newConfig);

  $.ajax("/config/config.js", { async: false, dataType: "text" }).done(
    (origConfig) => {
      setConfig(origConfig);
    }
  );

  const postConfig = () => {
    $("#saveButton").text("Saving...");
    $("#saveButton").attr({ disabled: true });

    $.post("/setConfig", { data: config, dataType: "text" }).done(() => {
      $("#saveButton").attr({ disabled: false });
      $("#saveButton").text("Save Configuration");
    });
  };

  return (
    <>
      <AceEditor
        mode="javascript"
        theme="github"
        onChange={setConfig}
        name="config_editor"
        value={config}
        style={{
          width: "100%",
        }}
        editorProps={{
          $blockScrolling: true,
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
      >
        Save Configuration
      </button>
    </>
  );
}
