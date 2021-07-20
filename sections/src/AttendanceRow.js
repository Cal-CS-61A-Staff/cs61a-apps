// @flow strict

import React, { useState } from "react";
import Button from "react-bootstrap/Button";
import { AttendanceStatus } from "./models";
import type { AttendanceStatusType } from "./models";
import useSectionAPI from "./useSectionAPI";

type Props = {
  editable: boolean,
  status: ?AttendanceStatusType,
  sessionId: string,
  email: String,
};

const buttonColorMap = {
  present: "success",
  excused: "warning",
  absent: "danger",
};

export default function AttendanceRow({
  editable,
  status,
  sessionId,
  email,
}: Props) {
  const [currentStatus, setStatus] = useState(status);
  const setAttendance = useSectionAPI("set_attendance");
  return (
    <>
      {Object.entries(AttendanceStatus).map(([statusOption, text]) => (
        <span key={statusOption}>
          <Button
            size="sm"
            variant={
              statusOption === currentStatus
                ? buttonColorMap[statusOption]
                : `outline-${buttonColorMap[statusOption]}`
            }
            disabled={!editable && status !== statusOption}
            onClick={() => {
              if (sessionId != null && email != null) {
                const settingAttendance = async () => {
                  await setAttendance({
                    session_id: sessionId,
                    students: email,
                    status: statusOption,
                  });
                  setStatus(statusOption);
                };
                settingAttendance();
              }
            }}
          >
            {text}
          </Button>{" "}
        </span>
      ))}
    </>
  );
}
