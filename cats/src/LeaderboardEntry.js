import React from "react";
import "./LeaderboardEntry.css";

export default function LeaderboardEntry(props) {
  return (
    <div className="Entry">
      <span className="Rank">{props.rank}</span>
      <span className="Score">{props.score.toFixed(2)}</span>
      <span className="Name">{props.name}</span>
    </div>
  );
}
