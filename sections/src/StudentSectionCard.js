/* eslint-disable react/no-array-index-key */
// @flow strict

import { useContext, useState } from "react";
import * as React from "react";
import Button from "react-bootstrap/Button";

import Card from "react-bootstrap/Card";
import ListGroup from "react-bootstrap/ListGroup";
import { Link } from "react-router-dom";
import { sectionTitle } from "./models";
import type { Section } from "./models";
import StateContext from "./StateContext";
import Tags from "./Tags";
import useAPI from "./useStateAPI";

import EnterEnrollmentCodeModal from "./EnterEnrollmentCodeModal";

type Props = {
  section: Section,
};

export default function StudentSectionCard({
  section,
}: Props): React.MixedElement {
  const { config, currentUser, enrolledSection } = useContext(StateContext);
  const hasSpace = section.capacity > section.students.length;
  const enrolledInThisSection = enrolledSection?.id === section.id;

  const isStaff = currentUser?.isStaff;
  const teachingThisSection = currentUser?.email === section.staff?.email;

  const [enrolling, setEnrolling] = useState(false);

  const joinSection = useAPI("join_section");
  const claimSection = useAPI("claim_section");
  const unassignSection = useAPI("unassign_section");

  const slotText = (
    <>({section.capacity - section.students.length} slots left)</>
  );

  const title = sectionTitle(section);

  const joinSectionWorkflow = () => {
    if (section.needsEnrollmentCode) {
      setEnrolling(true);
    } else {
      joinSection({ target_section_id: section.id });
    }
  };

  const onEnrollmentCodeEntered = (enrollmentCode) => {
    setEnrolling(false);
    joinSection({
      target_section_id: section.id,
      enrollment_code: enrollmentCode,
    });
  };

  return (
    <>
      <Card
        border={enrolledInThisSection || teachingThisSection ? "primary" : null}
      >
        <Card.Body>
          <Card.Title>
            {isStaff &&
              (section.staff == null
                ? config.canTutorsChange && (
                    <Button
                      className="float-right"
                      size="sm"
                      onClick={() => claimSection({ section_id: section.id })}
                    >
                      Claim
                    </Button>
                  )
                : (section.staff.email === currentUser?.email
                    ? config.canTutorsChange
                    : config.canTutorsReassign) && (
                    <Button
                      className="float-right"
                      size="sm"
                      variant="danger"
                      onClick={() =>
                        unassignSection({ section_id: section.id })
                      }
                    >
                      Unassign
                    </Button>
                  ))}
            {!isStaff && <Tags tags={section.tags} />}
            {isStaff ? (
              <Link to={`/section/${section.id}`}>{title}</Link>
            ) : (
              title
            )}
          </Card.Title>
          <Card.Text>{section.description}</Card.Text>
        </Card.Body>
        <ListGroup variant="flush">
          {section.students.map((student, i) => (
            <ListGroup.Item
              key={i}
              active={student.email === currentUser?.email}
            >
              {enrolledInThisSection || isStaff ? student.name : "A student"}
            </ListGroup.Item>
          ))}
          {hasSpace && !isStaff && config.canStudentsChange ? (
            <ListGroup.Item
              disabled={enrolledInThisSection}
              action={!enrolledInThisSection}
              onClick={joinSectionWorkflow}
            >
              {enrolledInThisSection ? (
                <div>Switch to Section {slotText}</div>
              ) : (
                <span className="btn-link">
                  {enrolledSection == null
                    ? "Join Section"
                    : "Switch to Section"}{" "}
                  {slotText}
                </span>
              )}
            </ListGroup.Item>
          ) : null}
        </ListGroup>
      </Card>
      <EnterEnrollmentCodeModal
        show={enrolling}
        section={section}
        onClose={onEnrollmentCodeEntered}
      />
    </>
  );
}
