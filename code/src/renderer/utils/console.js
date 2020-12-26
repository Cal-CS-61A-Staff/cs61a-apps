import { send } from "./communication.js";
import { START_CONSOLE } from "../../common/communicationEnums.js";

export default function startConsole(onOutput, onErr, onHalt) {
  return send({ type: START_CONSOLE }, onOutput, onErr, onHalt);
}
