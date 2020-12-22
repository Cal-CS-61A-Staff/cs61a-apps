import React from "react";
import "./Category.css";
import CheckBox from "./CheckBox.js";
import ValueField from "./ValueField.js";

export default function Category(props) {
  const checkBoxes = props.category.optionalArgs.map((arg, index) => {
    if (arg.isValue) {
      return (
        <ValueField
          field={arg}
          key={index}
          onChange={(val) => props.setOption(arg.longForm, val)}
        />
      );
    } else {
      return (
        <CheckBox
          flag={arg}
          key={index}
          onChange={(val) => props.setOption(arg.longForm, val)}
        />
      );
    }
  });

  const className = `Category ${props.active ? "activated" : "deactivated"}`;

  return (
    <div className="col-lg-3">
      <div className={className} onClick={props.onClick}>
        <h3>{props.category.name}</h3>
        <div className="text-muted">{props.category.explanation}</div>
        <div>{checkBoxes}</div>
      </div>
    </div>
  );
}
