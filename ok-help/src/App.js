import React, { useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.min.js";
import "./App.css";
import GeneratedCommand from "./GeneratedCommand.js";
import CommandOptions from "./CommandOptions.js";
import OPTIONS from "./schema.js";

function App() {
  const [activeIndex, setActiveIndex] = useState(null);

  const [selectedOptions, setSelectedOptions] = useState(
    OPTIONS.map(() => ({}))
  );

  return (
    <div className="App container">
      <div className="row">
        <div className="col">
          <br />
          <h1 className="display-4">
            <strong>okpy</strong> Command Generator
          </h1>
        </div>
      </div>
      <GeneratedCommand
        options={OPTIONS[activeIndex]}
        selectedArgs={selectedOptions[activeIndex]}
      />
      <CommandOptions
        options={OPTIONS}
        activeIndex={activeIndex}
        setActiveIndex={setActiveIndex}
        selectedOptions={selectedOptions}
        setSelectedOptions={setSelectedOptions}
      />
    </div>
  );
}

export default App;
