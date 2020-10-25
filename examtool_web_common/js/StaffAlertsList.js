import React from "react";
import { Button, Card } from "react-bootstrap";
import { getToken } from "./auth";
import post from "./post";

export default function StaffAlertsList({ selectedExam, staffData, onUpdate }) {
  const deleteAnnouncement = (id) => {
    (async () => {
      const resp = await post("/delete_announcement", {
        id,
        exam: selectedExam,
        token: getToken(),
      });
      if (resp.ok) {
        const data = await resp.json();
        if (data.success) {
          onUpdate(data);
        }
      }
    })();
  };

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
          <div id={id}>
            <Card>
              <Card.Header>
                Announcement for {questionName || "the overall exam"}{" "}
                {offset && `(${base}+${offset})`}
                <Button
                  style={{ float: "right" }}
                  variant="primary"
                  onClick={() => deleteAnnouncement(id)}
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
