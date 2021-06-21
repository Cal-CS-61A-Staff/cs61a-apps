import React from "react";
import "react-select2-wrapper/css/select2.css";

import { Row, Col } from "react-bootstrap";
import StudentTargetSelector from "./StudentTargetSelector.js";
import UploadTargets from "./UploadTargets.js";
import AssignmentDetails from "./AssignmentDetails.js";
import ConfigEditor from "./ConfigEditor.js";
import RegradeRequests from "./RegradeRequests.js";

export default function StaffView({
  students,
  onSubmit,
  isAdmin,
  canExportGrades,
}) {
  if (canExportGrades && window.location.toString().includes("histogram")) {
    return <AssignmentDetails assignment="Labs" onLogin={onSubmit} />;
  }
  if (isAdmin && window.location.toString().includes("edit")) {
    return <ConfigEditor />;
  }
  if (window.location.toString().includes("regrades")) {
    return <RegradeRequests />;
  }
  return (
    <div>
      <Row>
        <Col>
          <StudentTargetSelector
            students={students}
            onSubmit={onSubmit}
            isAdmin={isAdmin}
            canExportGrades={canExportGrades}
          />
        </Col>
      </Row>
      {isAdmin ? <UploadTargets /> : <br />}
    </div>
  );
}
