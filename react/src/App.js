import React from "react";
import logo from "./logo.svg";
import "./App.css";

import { LiveProvider, LiveEditor, LiveError, LivePreview } from "react-live";

function App() {
  return (
    <LiveProvider code="<strong>Hello World!</strong>">
      <LiveEditor />
      <LiveError />
      <LivePreview />
    </LiveProvider>
  );
}

export default App;
