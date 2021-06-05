// @flow strict

import moment from "moment-timezone";
import * as React from "react";

export type ID = string;
export type Time = number;
export type EnrollmentCode = string;

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

export const TZ = "America/Los_Angeles";

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

export function nextSessionStartTime(section: Section, dayOffset: number = 0) {
  const time = moment.unix(section.startTime).tz(TZ);
  while (time.isBefore(moment().add(dayOffset, "days"))) {
    time.add(7, "days");
  }
  return time.local();
}

export function sessionStartTimes(section: Section) {
  let time = moment.unix(section.startTime).tz(TZ);
  const out = [];
  while (time.isBefore(moment().subtract(3, "days"))) {
    out.push(time.clone().local());
    time = time.clone().add(7, "days");
  }
  return out;
}

export function sectionInterval(section: Section): React.MixedElement {
  const isPT = moment.tz.guess() === TZ;
  const startTime = nextSessionStartTime(section);
  const endTime = startTime
    .clone()
    .add(section.endTime - section.startTime, "seconds");
  return (
    <>
      {startTime.format("dddd h:mma")} &rarr; {endTime.format("h:mma")}
      {!isPT && <> ({moment().tz(moment.tz.guess()).format("z")})</>}
    </>
  );
}
