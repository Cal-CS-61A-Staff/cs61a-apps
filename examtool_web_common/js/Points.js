import React from "react";

export default function Points({ points }) {
  return points !== null && <small>Points: {points}</small>;
}
