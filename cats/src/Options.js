import React from "react";
import "./Options.css";

export default function Options(props) {
  return (
    <>
      <CheckBox
        id="autoCorrectCheckBox"
        text="Enable Auto-Correct"
        value={props.autoCorrect}
        onChange={props.onAutoCorrectToggle}
      />
      <br />
      <RestartButton onClick={props.onRestart} />
    </>
  );
}

function CheckBox(props) {
  return (
    <div className="Options custom-control custom-checkbox">
      <input
        type="checkbox"
        className="custom-control-input"
        id={props.id}
        checked={props.value}
        onChange={props.onChange}
      />
      <label className="custom-control-label" htmlFor={props.id}>
        {props.text}
      </label>
    </div>
  );
}

function RestartButton(props) {
  return (
    <div className="Button">
      <button type="button" className="btn btn-primary" onClick={props.onClick}>
        Restart
      </button>
    </div>
  );
}
