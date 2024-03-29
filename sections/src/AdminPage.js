/* eslint-disable react/no-array-index-key,camelcase */
// @flow strict

import "bootstrap/dist/css/bootstrap.css";
import { useContext, useState } from "react";
import * as React from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Tab from "react-bootstrap/Tab";
import Table from "react-bootstrap/Table";
import Tabs from "react-bootstrap/Tabs";
import FormControl from "react-bootstrap/FormControl";
import InputGroup from "react-bootstrap/InputGroup";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import ReactMarkdown from "react-markdown";
import { Redirect } from "react-router-dom";
import StateContext from "./StateContext";
import ToggleSwitch from "./ToggleSwitch";
import useAPI from "./useStateAPI";

import ImportSectionsModal from "./ImportSectionsModal";

export default function AdminPage(): React.Node {
  const { config, currentUser } = useContext(StateContext);

  const [message, setMessage] = useState(config.message);

  const [importing, setImporting] = useState(false);

  const updateConfig = useAPI("update_config");
  const exportAttendance = useAPI(
    "export_attendance",
    ({ custom: { attendances, fileName } }) => {
      if (attendances == null || fileName == null) {
        return;
      }
      const element = document.createElement("a");
      element.setAttribute(
        "href",
        `data:text/plain;charset=utf-8,${encodeURIComponent(attendances)}`
      );
      element.setAttribute("download", fileName);

      element.style.display = "none";
      // eslint-disable-next-line no-unused-expressions
      document.body?.appendChild(element);
      element.click();
      // eslint-disable-next-line no-unused-expressions
      document.body?.removeChild(element);
    }
  );
  const remindTutorsToSetupZoomLinks = useAPI(
    "remind_tutors_to_setup_zoom_links"
  );
  const importSections = useAPI("import_sections");

  const onSheetURLEntered = (sheetURL) => {
    importSections({
      sheet_url: sheetURL,
    });
    setImporting(false);
  };

  if (!currentUser?.isStaff) {
    return <Redirect to="/" />;
  }

  return (
    <Container>
      <br />
      <Row>
        <Col>
          <Tabs defaultActiveKey="general">
            <Tab eventKey="general" title="General">
              <Table striped hover>
                <thead>
                  <tr>
                    <th>Option</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>
                      Should students be able to leave their section and join a
                      new one?
                    </td>
                    <td>
                      <ToggleSwitch
                        defaultChecked={config.canStudentsChange}
                        onChange={(can_students_change) => {
                          updateConfig({ can_students_change });
                        }}
                      />
                    </td>
                  </tr>
                  <tr>
                    <td>
                      Should tutors be able to leave their section, or claim new
                      unassigned sections?
                    </td>
                    <td>
                      <ToggleSwitch
                        defaultChecked={config.canTutorsChange}
                        onChange={(can_tutors_change) => {
                          updateConfig({ can_tutors_change });
                        }}
                      />
                    </td>
                  </tr>
                  <tr>
                    <td>
                      Should tutors be able to remove other tutors from their
                      sections?
                    </td>
                    <td>
                      <ToggleSwitch
                        defaultChecked={config.canTutorsReassign}
                        onChange={(can_tutors_reassign) => {
                          updateConfig({ can_tutors_reassign });
                        }}
                      />
                    </td>
                  </tr>
                </tbody>
              </Table>
              <p>
                Welcome message:
                <InputGroup>
                  <FormControl
                    as="textarea"
                    placeholder="Write a short welcome message for students"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                  />
                  <InputGroup.Append>
                    <Button
                      variant="outline-secondary"
                      onClick={() => updateConfig({ message })}
                    >
                      Save
                    </Button>
                  </InputGroup.Append>
                </InputGroup>
              </p>
              <p>
                Preview:
                <Alert variant="info">
                  <ReactMarkdown>{message}</ReactMarkdown>
                </Alert>
              </p>
              <p>
                <Button onClick={() => exportAttendance({ full: false })}>
                  Export Attendance Summary
                </Button>{" "}
                <Button
                  variant="secondary"
                  onClick={() => exportAttendance({ full: true })}
                >
                  Export Full Attendances
                </Button>
              </p>
              <p>
                <Button
                  variant="danger"
                  onClick={() => remindTutorsToSetupZoomLinks()}
                >
                  Remind Tutors to Setup Zoom Links
                </Button>{" "}
                <Button variant="secondary" onClick={() => setImporting(true)}>
                  Import Sections
                </Button>
              </p>
            </Tab>
          </Tabs>
        </Col>
      </Row>
      <ImportSectionsModal show={importing} onClose={onSheetURLEntered} />
    </Container>
  );
}
