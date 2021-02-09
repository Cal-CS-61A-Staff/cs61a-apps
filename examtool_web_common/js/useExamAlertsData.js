import { useEffect, useState } from "react";
import { getToken } from "./auth";
import post from "./post";
import useInterval from "./useInterval";

export default function useExamAlertsData(selectedExam, isStaff, setDeadline) {
  const [examData, setExamData] = useState(null);
  const [stale, setStale] = useState(false);
  const [audioQueue, setAudioQueue] = useState([]); // pop off the next audio to play
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  useEffect(() => {
    if (audioQueue.length > 0 && !isPlayingAudio) {
      const nextAudio = audioQueue[0];
      const sound = new Audio(`data:audio/mp3;base64,${nextAudio}`);
      setIsPlayingAudio(true);
      sound.play();
      sound.addEventListener("ended", () => {
        setAudioQueue((queue) => queue.slice(1));
        setIsPlayingAudio(false);
      });
    }
  }, [audioQueue, isPlayingAudio]);

  useInterval(async () => {
    if (examData) {
      try {
        const resp = await post(isStaff ? "fetch_staff_data" : "fetch_data", {
          token: getToken(),
          exam: selectedExam,
          receivedAudio: examData
            ? examData.announcements.map((x) => x.id)
            : null,
          latestTimestamp: examData.latestTimestamp,
        });
        if (resp.ok) {
          const data = await resp.json();
          if (data.success) {
            setStale(false);
            const newData = {};
            for (const [key, value] of Object.entries(data)) {
              if (key === "messages") {
                // messages are merged, not overwritten
                const lookup = new Map();
                for (const message of examData.messages) {
                  lookup.set(message.id, message);
                }
                // update lookup to merge in changes
                const newMessages = [];
                for (const message of data.messages) {
                  if (lookup.has(message.id)) {
                    lookup.set(message.id, message);
                  } else {
                    newMessages.push(message);
                  }
                }
                for (const message of examData.messages) {
                  newMessages.push(lookup.get(message.id));
                }
                newData.messages = newMessages;
              } else {
                newData[key] = value;
              }
            }
            setExamData(newData);
            if (!isStaff) {
              const newAudio = [];
              for (const { audio } of data.announcements) {
                if (audio) {
                  newAudio.push(audio);
                }
              }
              newAudio.reverse();
              setAudioQueue((queue) => queue.concat(newAudio));
            }
          }
        }
      } catch (e) {
        console.error(e);
        setStale(true);
      }
    }
  }, 10000);

  const connect = async () => {
    try {
      const ret = await post(isStaff ? "fetch_staff_data" : "fetch_data", {
        token: getToken(),
        exam: selectedExam,
        latestTimestamp: 0,
      });
      if (!ret.ok) {
        return `The exam server failed with error ${ret.status}. Please try again.`;
      }

      try {
        const data = await ret.json();

        if (!data.success) {
          return "The exam server responded but did not produce valid data. Please try again.";
        } else {
          setExamData(data);
          if (setDeadline) {
            setDeadline(
              data.endTime -
                Math.round(data.timestamp) +
                Math.round(new Date().getTime() / 1000) -
                2
            );
          }
        }
      } catch {
        return "The web server returned invalid JSON. Please try again.";
      }
    } catch {
      return "Unable to reach server, your network may have issues.";
    }

    return null;
  };

  const send = async (endpoint, args) => {
    try {
      const resp = await post(endpoint, {
        token: getToken(),
        exam: selectedExam,
        latestTimestamp: examData.latestTimestamp,
        ...args,
      });
      const data = await resp.json();
      if (!data.success) {
        throw Error();
      }
      setExamData(data);
    } catch (e) {
      console.error(e);
      return "Something went wrong. Please try again, or reload the page.";
    }
    return null;
  };

  return [examData, stale, connect, send];
}
