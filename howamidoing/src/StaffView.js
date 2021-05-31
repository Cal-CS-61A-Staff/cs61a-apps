import React from "react";
import "react-select2-wrapper/css/select2.css";

import { Row, Col } from "react-bootstrap";
import StudentTargetSelector from "./StudentTargetSelector.js";
import UploadTargets from "./UploadTargets.js";
import AssignmentDetails from "./AssignmentDetails.js";
import ConfigEditor from "./ConfigEditor.js";
import RegradeRequests from "./RegradeRequests.js";

export default function StaffView({ students, onSubmit, isAdmin }) {
  if (isAdmin && window.location.toString().includes("histogram")) {
    return <AssignmentDetails assignment="Labs" onLogin={onSubmit} />;
  }
  if (isAdmin && window.location.toString().endsWith("edit")) {
    return <ConfigEditor />;
  }
  if (window.location.toString().includes("regrades")) {
    return (
      <RegradeRequests
        getAll={isAdmin && window.location.toString().includes("for=all")}
      />
    );
  }
  return (
    <div>
      <Row>
        <Col>
          <StudentTargetSelector
            students={students}
            onSubmit={onSubmit}
            isAdmin={isAdmin}
          />
        </Col>
      </Row>
      {isAdmin ? <UploadTargets /> : <br />}
    </div>
  );
}
