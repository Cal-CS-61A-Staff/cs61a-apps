// @flow strict
import moment from "moment";
import React, { useState } from "react";
import Button from "react-bootstrap/Button";
import Card from "react-bootstrap/Card";
import Table from "react-bootstrap/Table";
import { Link } from "react-router-dom";
import styled from "styled-components";
import AddStudentModal from "./AddStudentModal";
import AttendanceRow from "./AttendanceRow";
import { nextSessionStartTime } from "./models";
import type {
  AttendanceStatusType,
  Person,
  SectionDetails,
  Session,
} from "./models";
import useSectionAPI from "./useSectionAPI";

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

  const [adding, setAdding] = useState(false);

  const mostRecentSession =
    section.sessions.length > 0
      ? section.sessions[section.sessions.length - 1]
      : null;

  const notStartedSectionExists =
    mostRecentSession == null ||
    moment().isAfter(moment.unix(mostRecentSession.startTime).add(3, "days"));

  // if the latest section recently occurred, it is still "latest", not the one in the future
  const latestSectionStartTime = nextSessionStartTime(section, -3);

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
                ? latestSectionStartTime
                : moment.unix(session?.startTime)
              ).format("MMMM D")}
              {session == null && " (not started)"}
            </b>
            {session == null ? (
              <Button
                variant="primary"
                size="sm"
                onClick={() =>
                  startSession({
                    section_id: section.id,
                    start_time: latestSectionStartTime.unix(),
                  })
                }
              >
                Start Session
              </Button>
            ) : (
              <Button
                variant="outline-secondary"
                size="sm"
                onClick={() => setAdding(true)}
              >
                Add Student
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
      {session != null && (
        <AddStudentModal
          show={adding}
          onAdd={(student) =>
            setAttendance({
              session_id: session.id,
              student,
              status: ("present": AttendanceStatusType),
            })
          }
          onClose={() => setAdding(false)}
        />
      )}
    </>
  );
}
