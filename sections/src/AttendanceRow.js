// @flow strict

import React, {useState} from "react";
import Button from "react-bootstrap/Button";
import { AttendanceStatus } from "./models";
import type { AttendanceStatusType } from "./models";

type Props = {
  editable: boolean,
  status: ?AttendanceStatusType,
  onClick?: (AttendanceStatusType) => void,
};

const buttonColorMap = {
  present: "success",
  excused: "warning",
  absent: "danger",
};

export default function AttendanceRow({ editable, status, onClick }: Props) {
  const [currentStatus, setStatus] = useState(status);
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
              setStatus(statusOption);
              return onClick && onClick(((statusOption: any): AttendanceStatusType));
            }
              

            }
          >
            {text}
          </Button>{" "}
        </span>
      ))}
    </>
  );
}
