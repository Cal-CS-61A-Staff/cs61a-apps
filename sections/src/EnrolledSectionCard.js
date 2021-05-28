/* eslint-disable no-nested-ternary,react/no-array-index-key */
// @flow strict

import { useContext, useState, useEffect } from "react";
import Button from "react-bootstrap/Button";
import Card from "react-bootstrap/Card";
import * as React from "react";
import FormControl from "react-bootstrap/FormControl";
import { Link } from "react-router-dom";
import { nextSessionStartTime, sectionInterval } from "./models";
import type { Section, EnrollmentCode } from "./models";
import StateContext from "./StateContext";
import Tags from "./Tags";
import useStateAPI from "./useStateAPI";
import useAPI from "./useAPI";

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
  const nextText = `The next session takes place ${nextSessionStartTime(
    section
  ).fromNow()}.`;

  const state = useContext(StateContext);

  const isStaff = state.currentUser?.isStaff;

  const abandonSection = useStateAPI("unassign_section");
  const leaveSection = useStateAPI("leave_section");
  const updateSectionDescription = useStateAPI("update_section_description");
  const updateSectionCallLink = useStateAPI("update_section_call_link");
  const updateSectionEnrollmentCode = useStateAPI(
    "update_section_enrollment_code",
    () => getEnrollmentCode({ section_id: section.id })
  );
  const getEnrollmentCode = useAPI(
    "get_enrollment_code",
    (code: EnrollmentCode) => {
      setEnrollmentCode(code);
      setCurrentEnrollmentCode(code);
    }
  );

  useEffect(() => {
    if (isStaff) {
      getEnrollmentCode({ section_id: section.id });
    }
  }, []);

  const [description, setDescription] = useState(section.description ?? "");
  const [callLink, setCallLink] = useState(section.callLink ?? "");
  const [enrollmentCode, setEnrollmentCode] = useState(""); // in the text field
  const [currentEnrollmentCode, setCurrentEnrollmentCode] = useState(""); // in the db

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
            <Card.Text>
              <FormControl
                placeholder="Enrollment Code (optional)"
                value={enrollmentCode ?? ""}
                onChange={(e) => setEnrollmentCode(e.target.value)}
              />
            </Card.Text>
            {enrollmentCode !== currentEnrollmentCode && (
              <Card.Text>
                <Button
                  size="sm"
                  onClick={() => {
                    updateSectionEnrollmentCode({
                      section_id: section.id,
                      enrollment_code: enrollmentCode,
                    });
                  }}
                >
                  Submit
                </Button>
              </Card.Text>
            )}
          </>
        )}
        {isStaff === false && (
          <p>
            You have enrolled in{" "}
            {section.staff == null ? "a" : `${section.staff.name}'s`} tutorial!{" "}
            {nextText}
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
