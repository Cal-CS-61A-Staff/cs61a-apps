import * as React from "react";
import * as ReactDOM from "react-dom";

import "ace-builds/src-noconflict/ace";
import AceEditor from "react-ace";

import "ace-builds/src-noconflict/mode-python";
import "ace-builds/src-noconflict/ext-language_tools";
import "ace-builds/src-min-noconflict/ext-searchbox";

import "ace-builds/src-noconflict/mode-scheme";
import "ace-builds/src-noconflict/mode-sql";
import "ace-builds/src-noconflict/theme-merbivore_soft";

import firebase from "firebase/app";
import "firebase/database";
import firepad from "firepad/dist/firepad.min";
import { randomString } from "../../common/misc";
import glWrap from "../utils/glWrap.js";

import "firepad/dist/firepad.css";

function Editor({
  glContainer,
  text,
  debugData,
  language,
  shareRef,
  onChange,
  onActivate,
}) {
  const editorRef = React.useRef();

  const [displayLanguage, setDisplayLanguage] = React.useState(language);

  React.useEffect(() => {
    glContainer.on("show", () => onActivate());
    editorRef.current.editor.focus();
    editorRef.current.editor.getSession().setUseSoftTabs(true);
    onActivate();
    glContainer.on("resize", () => editorRef.current.editor.resize());
  }, []);

  React.useEffect(() => {
    setDisplayLanguage(language);
  }, [language]);

  // eslint-disable-next-line consistent-return
  React.useEffect(() => {
    if (shareRef) {
      const firebaseConfig = {
        apiKey: "AIzaSyB3_sakcABP6xn6sMBFLCCxDiL-HsK-ii8",
        authDomain: "cs61a-182bc.firebaseapp.com",
        databaseURL: "https://cs61a-182bc.firebaseio.com",
        projectId: "cs61a-182bc",
        storageBucket: "cs61a-182bc.appspot.com",
        messagingSenderId: "920393673645",
        appId: "1:920393673645:web:a0ba9e158cec4abffa0f24",
      };

      editorRef.current.editor.setValue("", 1);
      const app = firebase.initializeApp(firebaseConfig, randomString());
      const pad = firepad.fromACE(
        firebase.database(app).ref(shareRef),
        editorRef.current.editor
      );

      pad.on("ready", () => {
        if (!pad.getText()) {
          pad.setText(text);
        }
      });
      return () => pad.dispose();
    }
  }, [shareRef]);

  const code = debugData ? debugData.code : text;

  const markers = debugData
    ? [
        {
          startRow: debugData.line - 1,
          startCol: 0,
          endRow: debugData.line - 1,
          type: "fullLine",
          className: "activeLine",
        },
      ]
    : [];

  return ReactDOM.createPortal(
    <AceEditor
      mode={displayLanguage.toLowerCase()}
      theme="merbivore_soft"
      ref={editorRef}
      value={code}
      onChange={(newValue) => onChange(newValue)}
      name="editor-component"
      width="100%"
      height="100%"
      fontSize={14}
      readOnly={debugData && debugData.code !== text}
      setOptions={{
        enableBasicAutocompletion: true,
        enableLiveAutocompletion: true,
      }}
      markers={markers}
    />,
    glContainer.getElement().get(0)
  );
}

export default glWrap(Editor, "top", 50, "editor", ["editor"]);
