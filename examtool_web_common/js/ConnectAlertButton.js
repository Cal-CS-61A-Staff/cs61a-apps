import React, { useState } from "react";
import FailText from "./FailText";
import LoadingButton from "./LoadingButton";

export default function ConnectAlertButton({ onDownloadClick }) {
  const [loading, setLoading] = useState(false);

  const [failText, setFailText] = useState("");

  const download = async () => {
    setLoading(true);
    setFailText("");
    const err = await onDownloadClick();
    if (err) {
      setFailText(err);
    }
    setLoading(false);
  };

  return (
    <>
      <LoadingButton onClick={download} disabled={loading} loading={loading}>
        Connect to Server
      </LoadingButton>
      <FailText text={failText} suffixType="alerts" />
    </>
  );
}
