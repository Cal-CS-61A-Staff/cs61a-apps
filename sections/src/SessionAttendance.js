// @flow strict
import moment from "moment";
import React, { useMemo } from "react";
import Button from "react-bootstrap/Button";
import Card from "react-bootstrap/Card";
import Table from "react-bootstrap/Table";
import styled from "styled-components";
import type { AttendanceStatusType, SectionDetails, Session } from "./models";
import useSectionAPI from "./useSectionAPI";

import { AttendanceStatus } from "./models";

const TableHolder = styled.div`
  margin-bottom: -1em;
`;

const CardHeader = styled.div`
  display: flex;
  width: 100%;
  justify-content: space-between;
  align-items: center;
`;

type Props = {
  section: SectionDetails,
  session?: ?Session,
};

export default function SectionAttendance({ section, session }: Props) {
  const startSession = useSectionAPI("start_session");
  const setAttendance = useSectionAPI("set_attendance");

  const buttonColorMap = {
    present: "success",
    excused: "warning",
    absent: "danger",
  };

  const mostRecentSession =
    section.sessions.length > 0
      ? section.sessions[section.sessions.length - 1]
      : null;

  const nextSessionStartTime = useMemo(() => {
    const time = moment.unix(section.startTime);
    while (time.isBefore(moment().subtract(3, "days"))) {
      time.add(7, "days");
    }
    return time;
  }, [section]);

  if (
    session == null &&
    mostRecentSession != null &&
    moment().isBefore(moment.unix(mostRecentSession.startTime).add(3, "days"))
  ) {
    return null;
  }

  const getStudentAttendanceStatus = (email: string): ?AttendanceStatusType => {
    if (session == null) {
      return null;
    }
    for (const attendance of session.attendances) {
      if (attendance.student.email === email) {
        return attendance.status;
      }
    }
    return null;
  };

  return (
    <>
      <br />
      <Card>
        <Card.Header>
          <CardHeader>
            <b>
              {(session == null
                ? nextSessionStartTime
                : moment.unix(session?.startTime)
              ).format("MMMM D")}
              {session == null && " (not started)"}
            </b>
            {session == null && (
              <Button
                variant="primary"
                size="sm"
                onClick={() =>
                  startSession({
                    section_id: section.id,
                    start_time: nextSessionStartTime.unix(),
                  })
                }
              >
                Start Session
              </Button>
            )}
          </CardHeader>
        </Card.Header>
        <TableHolder>
          <Table>
            <tbody>
              {section.students.map((student) => (
                <tr key={student.email} className="text-center">
                  <td className="align-middle">{student.name}</td>
                  <td>
                    {Object.entries(AttendanceStatus).map(([status, text]) => (
                      <span key={status}>
                        <Button
                          size="sm"
                          variant={
                            getStudentAttendanceStatus(student.email) === status
                              ? buttonColorMap[status]
                              : `outline-${buttonColorMap[status]}`
                          }
                          disabled={session == null}
                          onClick={() =>
                            session != null &&
                            setAttendance({
                              session_id: session.id,
                              student: student.email,
                              status,
                            })
                          }
                        >
                          {text}
                        </Button>{" "}
                      </span>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </TableHolder>
      </Card>
    </>
  );
}
