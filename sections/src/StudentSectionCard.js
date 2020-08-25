// @flow strict

import { useContext } from "react";
import * as React from "react";
import Button from "react-bootstrap/Button";

import Card from "react-bootstrap/Card";
import ListGroup from "react-bootstrap/ListGroup";
import { sectionTitle } from "./models";
import type { Section } from "./models";
import StateContext from "./StateContext";
import Tags from "./Tags";
import useAPI from "./useAPI";

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

  const joinSection = useAPI("join_section");
  const claimSection = useAPI("claim_section");
  const unassignSection = useAPI("unassign_section");

  const slotText = (
    <>({section.capacity - section.students.length} slots left)</>
  );

  return (
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
                    onClick={() => unassignSection({ section_id: section.id })}
                  >
                    Unassign
                  </Button>
                ))}
          {!isStaff && <Tags tags={section.tags} />}
          {sectionTitle(section)}
        </Card.Title>
        <Card.Text>{section.description}</Card.Text>
      </Card.Body>
      <ListGroup variant="flush">
        {section.students.map((student, i) => (
          <ListGroup.Item key={i} active={student.email === currentUser?.email}>
            {enrolledInThisSection || isStaff ? student.name : "A student"}
          </ListGroup.Item>
        ))}
        {hasSpace && !isStaff && config.canStudentsChange ? (
          <ListGroup.Item
            disabled={enrolledInThisSection}
            action={!enrolledInThisSection}
            onClick={() => joinSection({ target_section_id: section.id })}
          >
            {enrolledInThisSection ? (
              <div>Switch to Section {slotText}</div>
            ) : (
              <a href="#">
                {enrolledSection == null ? "Join Section" : "Switch to Section"}{" "}
                {slotText}
              </a>
            )}
          </ListGroup.Item>
        ) : null}
      </ListGroup>
    </Card>
  );
}
