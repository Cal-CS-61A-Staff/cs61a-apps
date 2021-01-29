// @flow
import React from "react";
import Button from "react-bootstrap/Button";

export default function ResetButton({ onClick }: { onClick: () => mixed }) {
  return (
    <Button variant="secondary" onClick={onClick}>
      New Game
    </Button>
  );
}
