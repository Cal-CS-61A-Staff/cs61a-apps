import React from "react";
import "./Character.css";

export default function Character(props) {
  let className = "Character ";
  if (props.correct) {
    className += "correct";
  } else if (props.wrong) {
    className += "wrong";
  }
  return <span className={className}>{props.char}</span>;
}
