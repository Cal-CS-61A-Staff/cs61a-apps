import React, { useState } from "react";
import { Form } from "react-bootstrap";
import FailText from "./FailText";
import LoadingButton from "./LoadingButton";

export default function StaffMessageReplyBox({ compact, message, send }) {
  const [reply, setReply] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [failText, setFailText] = useState("");

  const submit = async (reject) => {
    setIsLoading(true);
    const err = await send("send_response", {
      id: message,
      reply: compact
        ? reject
          ? "Staff cannot answer this question"
          : "Staff has read your message"
        : reply,
    });
    if (err) {
      setFailText(err);
    } else {
      setReply("");
    }
    setIsLoading(false);
  };

  return (
    <>
      {!compact && (
        <Form.Group>
          <Form.Control
            as="textarea"
            rows={3}
            value={reply}
            placeholder="Reply to the private message."
            onChange={(e) => setReply(e.target.value)}
          />
        </Form.Group>
      )}
      <Form.Group>
        <LoadingButton
          loading={isLoading}
          disabled={isLoading}
          onClick={submit}
          size={compact && "sm"}
          variant={compact ? "warning" : "primary"}
        >
          {compact ? "✔" : "Send"}
        </LoadingButton>
        {compact && (
          <LoadingButton
            loading={isLoading}
            disabled={isLoading}
            onClick={() => submit(true)}
            size={compact && "sm"}
            variant="secondary"
          >
            ✖
          </LoadingButton>
        )}
        <FailText text={failText} suffixType="alerts" />
      </Form.Group>
    </>
  );
}
