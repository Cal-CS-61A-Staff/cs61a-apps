import React, { useState } from "react";
import { Form } from "react-bootstrap";
import { getToken } from "./auth";
import FailText from "./FailText";
import LoadingButton from "./LoadingButton";
import post from "./post";

export default function CourseSelector({ onSuccess }) {
  const [course, setCourse] = useState("");
  const [loading, setLoading] = useState(false);
  const [failText, setFailText] = useState("");

  const fail = () => {
    setFailText("Forbidden.");
    setLoading(false);
  };

  const submit = async () => {
    setLoading(true);
    try {
      const ret = await post("is_valid", {
        course,
        token: getToken(),
      });
      if (!ret.ok) {
        fail();
        return;
      }
      const data = await ret.json();
      if (!data.success) {
        fail();
        return;
      }
      onSuccess(course);
      setLoading(false);
    } catch {
      fail();
    }
  };

  return (
    <>
      Please enter your course code:
      <Form.Group>
        <Form.Control
          value={course}
          onChange={(e) => setCourse(e.target.value)}
          placeholder="cs61a"
        />
      </Form.Group>
      <LoadingButton onClick={submit} disabled={loading} loading={loading}>
        Authorize
      </LoadingButton>
      <FailText text={failText} />
    </>
  );
}
