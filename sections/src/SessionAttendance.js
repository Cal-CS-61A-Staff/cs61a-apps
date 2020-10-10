// @flow strict
import moment from "moment";
import React, { useMemo } from "react";
import Button from "react-bootstrap/Button";
import Card from "react-bootstrap/Card";
import Table from "react-bootstrap/Table";
import { Link } from "react-router-dom";
import styled from "styled-components";
import AttendanceRow from "./AttendanceRow";
import type {
  AttendanceStatusType,
  Person,
  SectionDetails,
  Session,
} from "./models";
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

  const notStartedSectionExists =
    mostRecentSession == null ||
    moment().isAfter(moment.unix(mostRecentSession.startTime).add(3, "days"));

  if (session == null && !notStartedSectionExists) {
    return null;
  }

  const sessionStudents: Array<Person> =
    session?.attendances.map((attendance) => attendance.student) ?? [];

  const students = Array.from(
    new Map(
      (session == null ||
      (session?.id === mostRecentSession?.id && !notStartedSectionExists)
        ? section.students.concat(sessionStudents)
        : sessionStudents
      ).map((student) => [student.email, student])
    ).values()
  ).sort((a, b) => a.name.localeCompare(b.name));

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
              {students.map((student) => (
                <tr key={student.email} className="text-center">
                  <td className="align-middle">
                    <Link to={`/user/${student.id}`}>{student.name}</Link>
                  </td>
                  <td>
                    <AttendanceRow
                      editable={session != null}
                      status={getStudentAttendanceStatus(student.email)}
                      onClick={(status) => {
                        if (session != null)
                          setAttendance({
                            session_id: session.id,
                            student: student.email,
                            status,
                          });
                      }}
                    />
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
