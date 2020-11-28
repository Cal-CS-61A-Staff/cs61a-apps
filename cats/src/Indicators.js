import React from "react";
import "./Indicators.css";
import Indicator from "./Indicator";
import { formatNum } from "./utils";

export default function Indicators({ wpm, accuracy, remainingTime }) {
  return (
    <div className="Indicators">
      <Indicator text={`WPM: ${formatNum(wpm)}`} />
      <Indicator text={`Accuracy: ${formatNum(accuracy)}`} />
      <Indicator text={`Time: ${remainingTime}`} />
    </div>
  );
}
