// @flow strict

import moment from "moment-timezone";
import * as React from "react";

export type ID = string;
export type Time = number;

export type Person = {
  id: ID,
  name: string,
  email: string,
  backupURL: string,
  isStaff: boolean,
};

export type PersonDetails = {
  ...Person,
  isAdmin?: boolean,
  // eslint-disable-next-line no-use-before-define
  attendanceHistory: Array<AttendanceDetails>,
};

export type Section = {
  id: ID,
  staff: ?Person,
  students: Array<Person>,
  description: string,
  capacity: number,
  startTime: Time,
  endTime: Time,
  callLink: ?string,
  tags: Array<string>,
};

const AttendanceStatus = {
  present: "Present",
  excused: "Excused",
  absent: "Absent",
};

export { AttendanceStatus };

export type AttendanceStatusType = $Keys<typeof AttendanceStatus>;

type Attendance = {
  student: Person,
  status: AttendanceStatusType,
};

export type Session = {
  id: ID,
  startTime: Time,
  attendances: Array<Attendance>,
};

type AttendanceDetails = {
  ...Attendance,
  section: ?Section,
  session: Session,
};

export type SectionDetails = {
  ...Section,
  sessions: Array<Session>,
};

export type CourseConfig = {
  canStudentsChange: boolean,
  canTutorsChange: boolean,
  canTutorsReassign: boolean,
  message: string,
};

export type State = {
  enrolledSection: ?Section,
  sections: Array<Section>,
  taughtSections: Array<Section>,
  currentUser: ?PersonDetails,
  config: CourseConfig,
};

export function sectionTitle(section: ?Section): React.MixedElement {
  return section == null ? (
    <>Deleted Section</>
  ) : (
    <>
      {section.staff == null
        ? "Unknown Tutor"
        : `${section.staff.name}'s section`}{" "}
      (#{section.id})
    </>
  );
}

export function sectionInterval(section: Section): React.MixedElement {
  const isPT = moment.tz.guess() === "America/Los_Angeles";
  const weeks = moment().diff(moment.unix(section.startTime), "weeks");
  return (
    <>
      {moment
        .unix(section.startTime)
        .add(weeks, "weeks")
        .local()
        .format("dddd h:mma")}{" "}
      &rarr;{" "}
      {moment.unix(section.endTime).add(weeks, "weeks").local().format("h:mma")}
      {!isPT && <> ({moment().tz(moment.tz.guess()).format("z")})</>}
    </>
  );
}
