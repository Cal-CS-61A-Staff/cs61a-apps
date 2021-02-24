import { createContext } from "react";

const ExamContext = createContext({
  exam: "",
  savedAnswers: {},
  onInternetError: () => null,
  recordUnsaved: () => null,
  recordSaved: () => null,
  recordSolved: () => null,
  recordUnsolved: () => null,
  setStarred: () => null,
  unsavedQuestions: new Set(),
  solvedQuestions: new Map(),
  starredQuestions: new Map(),
});

export default ExamContext;
