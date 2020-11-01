import React from "react";

const examSuffix =
  "If this error persists, contact your course staff or use the alternative exam medium.";

const alertsSuffix = "";

export default function FailText({ text, suffixType }) {
  return (
    <div style={{ color: "red" }}>
      {text}{" "}
      {text && { exam: examSuffix, alerts: alertsSuffix }[suffixType || "exam"]}
    </div>
  );
}
