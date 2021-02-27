import React, { useState } from "react";
import { getAuthParams } from "./auth";
import FailText from "./FailText";
import LoadingButton from "./LoadingButton";
import post from "./post";

export default function ExamDownloader({ exam, onReceive }) {
  const [loading, setLoading] = useState(false);

  const [failText, setFailText] = useState("");

  const download = async () => {
    setLoading(true);
    setFailText("");
    try {
      const ret = await post("get_exam", { ...getAuthParams(), exam });
      if (!ret.ok) {
        setFailText(`
                The exam server failed with error ${ret.status}. Please try again. 
            `);
      }

      try {
        const data = await ret.json();

        if (!data.success) {
          setFailText(`
                    The exam server responded but did not produce a valid exam. Please try again. 
                `);
        } else {
          onReceive(data);
        }
      } catch {
        setFailText("The web server returned invalid JSON. Please try again.");
      }
    } catch {
      setFailText("Unable to reach server, your network may have issues.");
    }

    setLoading(false);
  };

  return (
    <>
      <LoadingButton onClick={download} disabled={loading} loading={loading}>
        Generate Exam
      </LoadingButton>
      <FailText text={failText} />
    </>
  );
}
