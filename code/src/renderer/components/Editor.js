import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as React from "react";
import * as ReactDOM from "react-dom";

import AceEditor from "react-ace";

import "ace-builds/src-noconflict/ext-language_tools";
import "ace-builds/src-min-noconflict/ext-searchbox";

import "ace-builds/src-noconflict/mode-python";
import "ace-builds/src-noconflict/mode-scheme";
import "ace-builds/src-noconflict/mode-sql";
import "ace-builds/src-noconflict/mode-cirru";

import "ace-builds/src-noconflict/theme-merbivore_soft";

import firebase from "firebase/app";
import "firebase/database";
import firepad from "firepad/dist/firepad.min";
import { useDelayed } from "../utils/hooks";
import { LARK, SCHEME } from "../../common/languages";
import { randomString } from "../../common/misc";
import glWrap from "../utils/glWrap.js";

import "firepad/dist/firepad.css";

const PureAceEditor = React.memo(AceEditor);

function Editor({
  glContainer,
  text,
  debugData,
  language,
  shareRef,
  enableAutocomplete,
  onChange,
  onActivate,
}) {
  const editorRef = useRef();
  const markers = [];

  useEffect(() => {
    glContainer.on("show", () => onActivate());
    editorRef.current.editor.focus();
    editorRef.current.editor.getSession().setUseSoftTabs(true);
    onActivate();
    glContainer.on("resize", () => editorRef.current.editor.resize());
  }, []);

  // eslint-disable-next-line consistent-return
  useEffect(() => {
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

  if (debugData) {
    markers.push({
      startRow: debugData.line - 1,
      startCol: 0,
      endRow: debugData.line - 1,
      type: "fullLine",
      className: "activeLine",
    });
  }

  const [bracketMarker, setBracketMarker] = useState();

  if (bracketMarker) {
    markers.push(bracketMarker);
  }

  const handleCursorChange = useCallback(() => {
    const { editor } = editorRef.current;
    if (language !== SCHEME) {
      return;
    }
    let matchingBracket = getMatchingBracket(editor);
    setBracketMarker(null);
    if (matchingBracket != null) {
      let currentPos = editor.getCursorPosition();

      if (
        currentPos.row > matchingBracket.row ||
        (currentPos.row === matchingBracket.row &&
          currentPos.column > matchingBracket.column)
      ) {
        const temp = currentPos;
        currentPos = matchingBracket;
        matchingBracket = temp;
      }
      setBracketMarker({
        startRow: currentPos.row,
        startCol: currentPos.column,
        endRow: matchingBracket.row,
        endCol: matchingBracket.column,
        className: "ace_selection match_parens",
        type: editor.getSelectionStyle(),
      });
    }
  }, [language]);

  // useDelayed() needed so ace can update the data for one render before updating the language
  const displayLanguage = useDelayed(language === LARK ? "CIRRU" : language);
  const displayMarkers = useMemo(() => markers, [JSON.stringify(markers)]);

  const options = useMemo(
    () => ({
      enableBasicAutocompletion: enableAutocomplete,
      enableLiveAutocompletion: enableAutocomplete,
    }),
    [enableAutocomplete]
  );

  return ReactDOM.createPortal(
    <PureAceEditor
      mode={displayLanguage.toLowerCase()}
      theme="merbivore_soft"
      ref={editorRef}
      value={code}
      onChange={onChange}
      name="editor-component"
      className={language === SCHEME ? "scheme-editor" : "editor"}
      width="100%"
      height="100%"
      fontSize={14}
      readOnly={debugData && debugData.code !== text}
      setOptions={options}
      markers={displayMarkers}
      onCursorChange={handleCursorChange}
    />,
    glContainer.getElement().get(0)
  );
}

function getMatchingBracket(editor) {
  const cursor = editor.getCursorPosition();
  const index = editor.getSession().getDocument().positionToIndex(cursor);
  const nextVal = editor.getValue()[index];
  const prevVal = editor.getValue()[index - 1];

  if (prevVal === ")" || prevVal === "]") {
    return editor.getSession().findMatchingBracket(cursor, prevVal);
  } else if (nextVal === "(" || nextVal === "[") {
    cursor.column += 1;
    const out = editor.getSession().findMatchingBracket(cursor, nextVal);
    if (out !== null) {
      out.column += 1;
    }
    return out;
  }
  return null;
}

export default glWrap(Editor, "top", 50, "editor", ["editor"]);
