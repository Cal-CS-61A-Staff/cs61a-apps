import React from "react";

export default function ElementEntropy({ entropy }) {
  return (
    entropy != null && (
      <small style={{ color: "gray", marginTop: -5 }}>
        [version {entropy}]
      </small>
    )
  );
}
