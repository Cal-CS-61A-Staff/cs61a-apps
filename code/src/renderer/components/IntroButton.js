import React from "react";

export default function IntroButton(props) {
  return (
    <div className="introButton" onClick={props.onClick}>
      {props.name}
    </div>
  );
}
