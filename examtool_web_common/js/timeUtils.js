import { useExamData, useTime } from "./AlertsContext";

export function timeDeltaString(delta) {
  const hours = Math.floor(delta / 3600);
  const minutes = Math.floor((delta % 3600) / 60);
  const seconds = Math.floor(delta % 60);

  return `${hours ? `${hours}h ` : ""}${
    minutes ? `${minutes}m ` : ""
  }${seconds}s`;
}

export function timeDeltaMinutesString(delta) {
  const minutes = Math.floor(delta / 60);
  return `${minutes} minutes ago`;
}

export function useCurrentQuestion() {
  const time = useTime();
  const examData = useExamData();
  for (const question of examData.questions) {
    if (question.startTime <= time && time <= question.endTime) {
      return question;
    }
  }
  return null;
}

export function useNextQuestion() {
  const time = useTime();
  const examData = useExamData();
  let closestQuestion = null;
  for (const question of examData.questions) {
    if (question.startTime <= time) {
      continue;
    }
    if (
      closestQuestion == null ||
      question.startTime < closestQuestion.startTime
    ) {
      closestQuestion = question;
    }
  }
  return closestQuestion;
}
