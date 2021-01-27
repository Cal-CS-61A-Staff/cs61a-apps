import React from "react";
import Alert from "react-bootstrap/Alert";

export default function Commentary({ messages }: { messages: [string] }) {
  if (messages) {
    return messages.map((message, i) => {
      return (
        <Alert key={i} variant="dark">
          {message}
        </Alert>
      );
    });
  }
  return null;
}
