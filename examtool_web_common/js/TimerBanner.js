import React from "react";
import { Jumbotron } from "react-bootstrap";
import { useExamData, useTime } from "./AlertsContext";
import { timeDeltaString } from "./timeUtils";

export default function TimerBanner() {
  const time = useTime();
  const examData = useExamData();

  // eslint-disable-next-line no-nested-ternary
  const timeString =
    time < examData.startTime
      ? timeDeltaString(examData.startTime - time)
      : time < examData.endTime
      ? timeDeltaString(examData.endTime - time)
      : "Exam ended!";

  return (
    <Jumbotron>
      <h1 className="display-1 text-center">{timeString}</h1>
    </Jumbotron>
  );
}
