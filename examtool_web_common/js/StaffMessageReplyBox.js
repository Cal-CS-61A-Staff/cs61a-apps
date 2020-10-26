import React, { useState } from "react";
import { Form } from "react-bootstrap";
import { getToken } from "./auth";
import FailText from "./FailText";
import LoadingButton from "./LoadingButton";
import post from "./post";

export default function StaffMessageReplyBox({ exam, message, onUpdate }) {
  const [reply, setReply] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [failText, setFailText] = useState("");

  const submit = async () => {
    setIsLoading(true);
    try {
      const resp = await post("send_response", {
        exam,
        id: message,
        token: getToken(),
        reply,
      });
      const data = await resp.json();
      if (!data.success) {
        throw Error();
      }
      setReply("");
      onUpdate(data);
    } catch {
      setFailText(
        "Something went wrong. Reload the page to see if the reply was sent"
      );
    }
    setIsLoading(false);
  };

  return (
    <>
      <Form.Group>
        <Form.Control
          as="textarea"
          rows={3}
          value={reply}
          placeholder="Reply to the private message."
          onChange={(e) => setReply(e.target.value)}
        />
      </Form.Group>
      <Form.Group>
        <LoadingButton
          loading={isLoading}
          disabled={isLoading}
          onClick={submit}
        >
          Send
        </LoadingButton>
        <FailText text={failText} suffixType="alerts" />
      </Form.Group>
    </>
  );
}
