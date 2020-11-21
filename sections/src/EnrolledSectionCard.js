/* eslint-disable no-nested-ternary,react/no-array-index-key */
// @flow strict

import moment from "moment-timezone";
import { useContext, useMemo, useState } from "react";
import Button from "react-bootstrap/Button";
import Card from "react-bootstrap/Card";
import * as React from "react";
import FormControl from "react-bootstrap/FormControl";
import { Link } from "react-router-dom";
import { sectionInterval } from "./models";
import type { Section } from "./models";
import StateContext from "./StateContext";
import Tags from "./Tags";
import useAPI from "./useStateAPI";

type Props = {
  section: Section,
};

function sentenceList(items: Array<React.MixedElement>, isStaff: ?boolean) {
  const also = isStaff ? null : "also";
  if (items.length === 0) {
    return "No one else has joined this tutorial yet.";
  } else if (items.length === 1) {
    return (
      <>
        {items[0]} has {also} joined this tutorial.
      </>
    );
  } else if (items.length === 2) {
    return (
      <>
        {items[0]} and {items[1]} have {also} joined this tutorial.
      </>
    );
  } else {
    const allButLast = items.slice(0, items.length - 1);
    return (
      <>
        {allButLast.map((item, i) => (
          <span key={i}>{item}, </span>
        ))}
        and {items[items.length - 1]} have {also} joined this tutorial.
      </>
    );
  }
}

export default function EnrolledSectionCard({ section }: Props) {
  const [startTime, endTime] = useMemo(() => {
    const start = moment.unix(section.startTime).tz("America/Los_Angeles");
    const end = moment.unix(section.endTime).tz("America/Los_Angeles");
    const curr = moment();
    while (end < curr) {
      start.add(7, "days");
      end.add(7, "days");
    }
    return [start, end];
  }, [section]);

  const prevText = `The session started ${endTime.fromNow()}`;
  const nextText = `The next session takes place ${startTime.fromNow()}.`;

  const state = useContext(StateContext);

  const isStaff = state.currentUser?.isStaff;

  const abandonSection = useAPI("unassign_section");
  const leaveSection = useAPI("leave_section");
  const updateSectionDescription = useAPI("update_section_description");
  const updateSectionCallLink = useAPI("update_section_call_link");

  const [description, setDescription] = useState(section.description ?? "");
  const [callLink, setCallLink] = useState(section.callLink ?? "");

  return (
    <Card>
      <Card.Header>
        <h5 className="mb-n1">
          {sectionInterval(section)} (#{section.id})
          <Tags tags={section.tags} />
        </h5>
      </Card.Header>
      <Card.Body>
        {isStaff ? (
          <>
            <Card.Text>
              <FormControl
                as="textarea"
                placeholder="Introduce yourself!"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </Card.Text>
            {description !== section.description && (
              <Card.Text>
                <Button
                  size="sm"
                  onClick={() =>
                    updateSectionDescription({
                      section_id: section.id,
                      description,
                    })
                  }
                >
                  Save
                </Button>
              </Card.Text>
            )}
          </>
        ) : (
          <Card.Text>{section.description}</Card.Text>
        )}
        {isStaff && (
          <>
            <Card.Text>
              <FormControl
                placeholder="Your Zoom Link"
                value={callLink ?? ""}
                onChange={(e) => setCallLink(e.target.value)}
              />
            </Card.Text>
            {callLink !== section.callLink && (
              <Card.Text>
                <Button
                  size="sm"
                  variant="info"
                  href={callLink}
                  target="_blank"
                >
                  Test Link
                </Button>{" "}
                <Button
                  size="sm"
                  onClick={() =>
                    updateSectionCallLink({
                      section_id: section.id,
                      call_link: callLink,
                    })
                  }
                >
                  Save
                </Button>
              </Card.Text>
            )}
          </>
        )}
        {isStaff === false && (
          <p>
            You have enrolled in{" "}
            {section.staff == null ? "a" : `${section.staff.name}'s`} tutorial!{" "}
            {startTime.isAfter(moment()) ? nextText : prevText}
          </p>
        )}
        <p>
          {sentenceList(
            section.students
              .filter((student) => student.email !== state.currentUser?.email)
              .map((student) => <>{student.name}</>),
            isStaff
          )}
        </p>
        {section.callLink != null && (
          <p>
            {isStaff ? (
              <Link to={`/section/${section.id}`}>
                <Button variant="success" size="lg">
                  Enter Tutorial
                </Button>
              </Link>
            ) : (
              <Button
                variant="success"
                size="lg"
                href={isStaff ? null : section.callLink}
                target="_blank"
              >
                Enter Call
              </Button>
            )}
          </p>
        )}
        {(isStaff
          ? state.config.canTutorsChange
          : state.config.canStudentsChange) && (
          <Button
            variant="danger"
            size="sm"
            onClick={() =>
              isStaff
                ? abandonSection({ section_id: section.id })
                : leaveSection({ section_id: section.id })
            }
          >
            {isStaff ? "Abandon Tutorial" : "Leave Tutorial"}
          </Button>
        )}
      </Card.Body>
    </Card>
  );
}
