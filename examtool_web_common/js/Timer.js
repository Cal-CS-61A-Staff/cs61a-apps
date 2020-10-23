import React, { useState } from "react";
import { Button } from "react-bootstrap";
import useInterval from "./useInterval";

export default function Timer({ target, onLock, onEnd }) {
  const [visible, setVisible] = useState(false);
  const [hover, setHover] = useState(false);
  const [timeString, setTimeString] = useState("");

  const updateTimeString = () => {
    const time = Math.round(new Date().getTime() / 1000);
    const remaining = Math.max(target - time, 0);

    const hours = Math.floor(remaining / 3600);
    const minutes = Math.floor((remaining % 3600) / 60);
    const seconds = remaining % 60;

    setTimeString(
      `${hours.toString().padStart(2, "0")}:${minutes
        .toString()
        .padStart(2, "0")}` + `:${seconds.toString().padStart(2, "0")}`
    );

    if (target - time < 0 && target - time >= -60) {
      onLock();
      setTimeString(`${60 + target - time}s`);
    }

    if (target - time < -60) {
      onEnd();
    }
  };

  useInterval(updateTimeString, 1000);

  if (!timeString) {
    updateTimeString();
  }

  return (
    <Button
      style={{ minWidth: 80 }}
      onClick={() => setVisible(!visible)}
      variant="outline-light"
      className="ml-auto"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {/* eslint-disable-next-line no-nested-ternary */}
      {visible
        ? hover
          ? "Click to hide timer"
          : timeString
        : "Click to show timer"}
    </Button>
  );
}
