import { createContext, useContext } from "react";

const AlertsContext = createContext({
  time: 0,
  examData: {
    questions: [],
  },
  stale: false,
});

export default AlertsContext;

export function useTime() {
  return useContext(AlertsContext).time;
}

export function useExamData() {
  return useContext(AlertsContext).examData;
}
