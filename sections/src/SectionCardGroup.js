/* eslint-disable react/no-array-index-key */
// @flow strict

import { useState } from "react";
import * as React from "react";
import Card from "react-bootstrap/Card";
import styled from "styled-components";
import { sectionInterval } from "./models";
import type { Section } from "./models";
import StudentSectionCard from "./StudentSectionCard";

type Props = {
  sections: Array<Section>,
};

const FlexLayout = styled.div`
  display: flex;
`;

const FlexColumn = styled.div`
  width: 0;
  flex-grow: 1;
  margin: 0 12px;
`;

const CardHolder = styled.div`
  margin: 12px 0;
`;

const CardFooter = styled.div`
  :hover {
    background: lightgray;
    cursor: pointer;
  }
`;

export default function SectionCardGroup({
  sections,
}: Props): React.MixedElement {
  const [expanded, setExpanded] = useState(false);

  const cardsPerRow = window.innerWidth < 768 ? 1 : 3;

  const expandable = sections.length > cardsPerRow;

  const numHiddenOpenSections = sections
    .slice(cardsPerRow)
    .filter((section) => section.capacity > section.students.length).length;

  const columns = Array(cardsPerRow)
    .fill()
    .map((_, i) =>
      sections
        .slice(0, expanded ? sections.length : cardsPerRow)
        .map((section, j) => [section, j])
        .filter(([, j]) => j % cardsPerRow === i)
        .map(([section]) => section)
    );

  const body = (
    <FlexLayout>
      {columns.map((columnSections, i) => (
        <FlexColumn key={i}>
          {columnSections.map((section) => (
            <CardHolder key={section.id}>
              <StudentSectionCard section={section} />
            </CardHolder>
          ))}
        </FlexColumn>
      ))}
    </FlexLayout>
  );

  return (
    <>
      <h2>{sectionInterval(sections[0])}</h2>
      {expandable ? (
        <Card>
          <Card.Body>{body}</Card.Body>
          {expandable ? (
            <CardFooter onClick={() => setExpanded((x) => !x)}>
              <Card.Footer className="text-center">
                {expanded ? (
                  <>Hide extra sections</>
                ) : (
                  <>
                    Show {sections.length - cardsPerRow} more sections (
                    {numHiddenOpenSections} with open slots)
                  </>
                )}
              </Card.Footer>
            </CardFooter>
          ) : null}
        </Card>
      ) : (
        body
      )}
    </>
  );
}
