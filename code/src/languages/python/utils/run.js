import { RUN_PY_CODE, RUN_PY_FILE } from "../constants/communicationEnums.js";
import { send } from "../../../renderer/utils/communication.js";
import { PYTHON } from "../../../common/languages.js";

export function runPyCode(code, onOutput, onErr, onHalt) {
  return send(
    { handler: PYTHON, type: RUN_PY_CODE, code },
    onOutput,
    onErr,
    onHalt
  );
}

export function runPyFile(location, onOutput, onErr, onHalt) {
  return send(
    { handler: PYTHON, type: RUN_PY_FILE, location },
    onOutput,
    onErr,
    onHalt
  );
}
