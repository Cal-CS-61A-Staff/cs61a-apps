// @flow strict

import React from "react";
import Button from "react-bootstrap/Button";
import Card from "react-bootstrap/Card";
import styled from "styled-components";
import type { SectionDetails } from "./models";

const FlexLayout = styled.div`
  display: flex;
  flex-wrap: wrap;
`;

const CardHolder = styled.div`
  width: 300px;
  margin: 8px;
`;

type Props = {
  section: SectionDetails,
};

export default function SectionRoster({ section }: Props) {
  return (
    <FlexLayout>
      {section.students.map((student) => (
        <CardHolder key={student.email}>
          <Card>
            <Card.Body>
              <Card.Title>{student.name}</Card.Title>
              <Card.Text>
                <a href={`mailto:${student.email}`}>{student.email}</a>
              </Card.Text>
              <Button
                href={student.backupURL}
                target="_blank"
                variant="outline-dark"
                size="sm"
              >
                View Backups
              </Button>{" "}
              <Button variant="danger" size="sm">
                Remove
              </Button>
            </Card.Body>
          </Card>
        </CardHolder>
      ))}
    </FlexLayout>
  );
}
