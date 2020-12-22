import React from "react";
import useId from "./utils.js";

import "./ValueField.css";

export default function ValueField(props) {
  const id = useId();
  return (
    <div className="ValueField">
      <div className="form-group">
        <label htmlFor={id.current}>
          <b>{props.field.name}</b>
          <br />
          <small>{props.field.explanation}</small>
        </label>
        <input
          type="text"
          className="form-control"
          id={id.current}
          placeholder={props.field.placeholder}
          onChange={(e) => props.onChange(e.target.value)}
        />
      </div>
    </div>
  );
}
