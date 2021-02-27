import { getAuthParams } from "./auth";
import post from "./post";

function makePrefixes(exam) {
  const baseHistoryPrefix = "history:";
  const baseAnswerPrefix = "answerPrefix:";

  return {
    historyPrefix: `${exam}|${baseHistoryPrefix}|`,
    answerPrefix: `${exam}|${baseAnswerPrefix}|`,
  };
}

export function logAnswer(exam, questionID, value) {
  try {
    const { historyPrefix, answerPrefix } = makePrefixes(exam);
    localStorage.setItem(`${historyPrefix}${questionID}|${Date.now()}`, value);
    localStorage.setItem(`${answerPrefix}${questionID}`, value);
  } catch (e) {
    console.error(e);
  }
}

export async function synchronize(exam) {
  try {
    const history = {};
    const snapshot = {};
    const { historyPrefix, answerPrefix } = makePrefixes(exam);

    for (const [key, value] of Object.entries(localStorage)) {
      if (key.startsWith(historyPrefix)) {
        history[key.slice(historyPrefix.length)] = value;
        localStorage.removeItem(key);
      } else if (key.startsWith(answerPrefix)) {
        snapshot[key.slice(answerPrefix.length)] = value;
      }
    }
    post("backup_all", {
      exam,
      history,
      snapshot,
      ...getAuthParams(),
    });
  } catch (e) {
    console.error(e);
  }
}

window.synchronize = synchronize;
