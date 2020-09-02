// @flow strict

import * as React from "react";

import type { SectionDetails } from "./models";
import SessionAttendance from "./SessionAttendance";

type Props = {
  section: SectionDetails,
};

export default function SectionAttendance({ section }: Props) {
  return (
    <>
      <SessionAttendance section={section} />
      {section.sessions.slice().reverse().map((session) => (
        <SessionAttendance
          key={session.startTime}
          session={session}
          section={section}
        />
      ))}
    </>
  );
}
