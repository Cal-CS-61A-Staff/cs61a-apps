// @flow strict

import { useState } from "react";
import * as React from "react";
import Button from "react-bootstrap/Button";
import AddSessionModel from "./AddSessionModal";

import type { SectionDetails } from "./models";
import SessionAttendance from "./SessionAttendance";

type Props = {
  section: SectionDetails,
};

export default function SectionAttendance({ section }: Props) {
  const [adding, setAdding] = useState(false);

  return (
    <>
      <SessionAttendance section={section} />
      {section.sessions
        .slice()
        .reverse()
        .map((session) => (
          <SessionAttendance
            key={session.startTime}
            session={session}
            section={section}
          />
        ))}
      <p>
        <br />
        <Button variant="secondary" size="sm" onClick={() => setAdding(true)}>
          Add Missing Session
        </Button>
      </p>
      <AddSessionModel
        show={adding}
        section={section}
        onClose={() => setAdding(false)}
      />
    </>
  );
}
