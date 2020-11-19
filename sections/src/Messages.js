/* eslint-disable react/no-array-index-key */
// @flow strict

import * as React from "react";
import Alert from "react-bootstrap/Alert";

type Props = {
  messages: Array<string>,
  onChange: (Array<string>) => void,
};

export default function Messages({ messages, onChange }: Props) {
  const hideMessage = (i) =>
    onChange(messages.slice(0, i).concat(messages.slice(i + 1)));
  return (
    <>
      {messages.map((message, i) => (
        <Alert
          variant="danger"
          onClose={() => hideMessage(i)}
          dismissible
          key={i}
        >
          {message}
        </Alert>
      ))}
    </>
  );
}
