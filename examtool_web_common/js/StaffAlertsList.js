import React from "react";
import { Button, Card } from "react-bootstrap";

export default function StaffAlertsList({ staffData, send }) {
  const deleteAnnouncement = (id) => () => send("delete_announcement", { id });

  return (
    <>
      <h3>Public Announcements</h3>
      {staffData.announcements.map(
        ({
          base,
          id,
          offset,
          canonical_question_name: questionName,
          message,
          spoken_message: spokenMessage,
        }) => (
          <div key={id}>
            <Card>
              <Card.Header>
                Announcement for {questionName || "the overall exam"}{" "}
                {offset && `(${base}+${offset})`}
                <Button
                  style={{ float: "right" }}
                  variant="primary"
                  onClick={deleteAnnouncement(id)}
                  size="sm"
                >
                  Delete
                </Button>
              </Card.Header>
              <Card.Body>
                {message}
                {/* eslint-disable-next-line no-nested-ternary */}
                {spokenMessage === "" ? (
                  <i> [Silent]</i>
                ) : spokenMessage == null ? null : (
                  <i> [Audio Override: {spokenMessage}]</i>
                )}
              </Card.Body>
            </Card>
            <br />
          </div>
        )
      )}
    </>
  );
}
