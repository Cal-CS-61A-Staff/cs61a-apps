import React from "react";
import IntroButton from "./IntroButton";
import { PYTHON, SCHEME, SQL } from "../../common/languages.js";
import { extension } from "../utils/dispatch.js";

export default function IntroBox({ onCreateClick, onOpenClick }) {
  const handleClick = (language) => () => onCreateClick(extension(language));

  return (
    <div className="introHolder">
      <div className="introTitle">61A Code</div>
      <div className="versionNumber">v{VERSION}</div>
      <IntroButton name="Create new file" onClick={() => onCreateClick()} />
      <IntroButton name="Open existing file" onClick={onOpenClick} />
      <IntroButton
        name="Start Python interpreter"
        onClick={handleClick(PYTHON)}
      />
      <IntroButton
        name="Start Scheme interpreter"
        onClick={handleClick(SCHEME)}
      />
      <IntroButton name="Start SQL interpreter" onClick={handleClick(SQL)} />
    </div>
  );
}
