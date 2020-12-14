import React from "react";
import { Button, Spinner } from "react-bootstrap";

export default function LoadingButton({
  children,
  loading,
  disabled,
  onClick,
  style,
  variant = "primary",
  size = undefined,
}) {
  return (
    <Button
      variant={variant}
      onClick={onClick}
      disabled={disabled}
      style={style}
      size={size}
    >
      {loading && (
        <Spinner
          as="span"
          animation="border"
          size="sm"
          role="status"
          aria-hidden="true"
          style={{ marginRight: 10 }}
        />
      )}
      {children}
    </Button>
  );
}
