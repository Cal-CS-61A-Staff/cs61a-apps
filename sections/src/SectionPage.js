/* eslint-disable react/no-array-index-key */
// @flow strict

import "bootstrap/dist/css/bootstrap.css";
import { useContext, useEffect, useState } from "react";
import * as React from "react";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Tab from "react-bootstrap/Tab";
import Tabs from "react-bootstrap/Tabs";

import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import { Redirect } from "react-router-dom";
import { sectionInterval } from "./models";
import type { ID, SectionDetails } from "./models";
import SectionAttendance from "./SectionAttendance";
import SectionRoster from "./SectionRoster";
import SectionStateContext from "./SectionStateContext";
import StateContext from "./StateContext";
import Tags from "./Tags";
import useSectionAPI from "./useSectionAPI";

type Props = {
  id: ID,
};

export default function SectionPage({ id }: Props): React.Node {
  const state = useContext(StateContext);

  const [section, setSection] = useState<?SectionDetails>(null);

  const fetchSection = useSectionAPI("fetch_section", setSection);

  useEffect(() => {
    fetchSection({ section_id: id });
  }, [id, fetchSection]);

  if (!state.currentUser?.isStaff) {
    return <Redirect to="/" />;
  }

  if (section == null) {
    return null;
  }

  return (
    <SectionStateContext.Provider
      value={{ ...section, updateState: setSection }}
    >
      <Container>
        <br />
        <Row>
          <Col>
            <h1>
              Section #{section.id}
              <Tags tags={section.tags} />
            </h1>
            <p className="lead">{sectionInterval(section)}</p>
            {section.callLink != null && (
              <p>
                <Button
                  href={section.callLink}
                  target="_blank"
                  variant="success"
                >
                  Join Call
                </Button>
              </p>
            )}
          </Col>
        </Row>
        <Tabs defaultActiveKey="attendance" transition={false}>
          <Tab eventKey="attendance" title="Attendance">
            <SectionAttendance section={section} />
          </Tab>
          <Tab eventKey="roster" title="Roster">
            <SectionRoster section={section} />
          </Tab>
        </Tabs>
      </Container>
    </SectionStateContext.Provider>
  );
}
