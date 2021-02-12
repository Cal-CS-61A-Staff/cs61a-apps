import { getToken } from "./auth";
import post from "./post";

const historyPrefix = "history:";
const answerPrefix = "answerPrefix:";

export function logAnswer(questionID, value) {
  localStorage.setItem(`${historyPrefix}|${questionID}|${Date.now()}`, value);
  localStorage.setItem(`${answerPrefix}|${questionID}`, value);
}

export async function synchronize() {
  const history = {};
  for (const [key, value] of Object.entries(localStorage)) {
    if (key.startsWith(historyPrefix)) {
      history[key] = value;
      localStorage.removeItem(key);
    }
  }
  const ret = await post("backup_all", {
    id: question.id,
    value: val,
    sentTime: new Date().getTime(),
    token: getToken(),
    exam: examContext.exam,
  });
}

window.synchronize = synchronize;
