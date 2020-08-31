/* eslint-disable react/no-array-index-key */
// @flow strict

import * as React from "react";
import Button from "react-bootstrap/Button";

import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Jumbotron from "react-bootstrap/Jumbotron";
import moment from "moment-timezone";
import { useContext } from "react";
import Row from "react-bootstrap/Row";
import styles from "styled-components";
import EnrolledSectionCard from "./EnrolledSectionCard";

import type { Section, Time } from "./models";

import nullThrows from "./nullThrows";

import "bootstrap/dist/css/bootstrap.css";
import SectionCardGroup from "./SectionCardGroup";
import StateContext from "./StateContext";

const FlexLayout = styles.div`
  display: flex;
  align-items: center;
  height: 100%;
`;

export default function MainPage(): React.Node {
  const state = useContext(StateContext);

  const timeKeyLookup = new Map<string, [Time, Time]>();
  const sectionsGroupedByTime = new Map<string, Array<Section>>();

  for (const section of state.sections) {
    const interval = [section.startTime, section.endTime];
    const key = interval.toString();
    if (!sectionsGroupedByTime.has(key)) {
      sectionsGroupedByTime.set(key, []);
      timeKeyLookup.set(key, interval);
    }
    nullThrows(sectionsGroupedByTime.get(key)).push(section);
  }

  const sortedIntervals: Array<[Time, Time]> = Array.from(
    timeKeyLookup.values()
  ).sort(([s1, e1], [s2, e2]) =>
    // eslint-disable-next-line no-nested-ternary
    s1 < s2 || (s1 === s2 && e1 < e2) ? -1 : s1 === s2 && e1 === e2 ? 0 : 1
  );

	var time = moment();
	var aTime, bTime;

  return (
    <>
      <Jumbotron fluid>
        <Container>
          <Row>
            <Col>
              <h1 className="display-4">CS 61A Tutorials</h1>
            </Col>
            {state.currentUser == null ? (
              <Col>
                <FlexLayout>
                  <Button block variant="warning" size="lg" href="/oauth/login">
                    Sign in with OKPy
                  </Button>
                </FlexLayout>
              </Col>
            ) : null}
          </Row>
          {state.currentUser?.isStaff ? (
            state.taughtSections.sort((a, b) => (
							(aTime = moment.unix(a.endTime).diff(time)) &&
							(bTime = moment.unix(b.endTime).diff(time)) &&
							(aTime > bTime ? 1 : -1) * (aTime * bTime))
						).map((section, i) => (
              <div key={section.id}>
                {i !== 0 && <br />}
                <EnrolledSectionCard section={section} />
              </div>
            ))
          ) : state.enrolledSection == null ? null : (
            <EnrolledSectionCard section={state.enrolledSection} />
          )}
        </Container>
      </Jumbotron>
      <Container>
        {sortedIntervals.map(([start, end], i) => (
          <Row key={i}>
            <Col>
              <SectionCardGroup
                sections={nullThrows(
                  sectionsGroupedByTime.get([start, end].toString())
                )}
              />
              <br />
            </Col>
          </Row>
        ))}
      </Container>
    </>
  );
}
