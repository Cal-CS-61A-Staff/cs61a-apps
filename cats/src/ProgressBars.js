import React from "react";
import "./ProgressBars.css";
import ProgressBar from "react-bootstrap/ProgressBar";

export default function ProgressBars({ progress: allProgress, playerIndex }) {
  const variants = ["info", "warning", "success", "danger"];

  return (
    <div className="ProgressBars">
      {allProgress.map(([progress, time], index) => {
        const displayText = progress === 1 && `${time.toFixed(2)} seconds`;
        const playerSuffix = index === playerIndex ? " (you)" : "";
        return (
          <div className="ProgressBar" key={index}>
            <ProgressBar
              variant={variants[index]}
              animated
              label={`Player ${index + 1}${playerSuffix}`}
              now={progress * 100}
            />
            <div className="barData">{displayText}</div>
          </div>
        );
      })}
    </div>
  );
}
