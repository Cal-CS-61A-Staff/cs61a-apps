// @flow strict

import moment from "moment-timezone";
import * as React from "react";

export type Person = {
  name: string,
  email: string,
  backupURL: string,
  isStaff: boolean,
  isAdmin?: boolean,
};

export type ID = string;
export type Time = number;

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

export type SectionDetails = {
  ...Section,
  sessions: Array<Session>,
};

export type CourseConfig = {
  canStudentsChange: boolean,
  canTutorsChange: boolean,
  canTutorsReassign: boolean,
};

export type State = {
  enrolledSection: ?Section,
  sections: Array<Section>,
  taughtSections: Array<Section>,
  currentUser: ?Person,
  config: CourseConfig,
};

export function sectionTitle(section: Section): React.MixedElement {
  return (
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
  return (
    <>
      {moment.unix(section.startTime).local().format("dddd h:mma")} &rarr;{" "}
      {moment.unix(section.endTime).local().format("h:mma")}
      {!isPT && <> ({moment().tz(moment.tz.guess()).format("z")})</>}
    </>
  );
}
