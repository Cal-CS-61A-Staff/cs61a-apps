import { send } from "../../../renderer/utils/communication.js";
import { SCHEME } from "../../../common/languages.js";
import { RUN_SCM_CODE, RUN_SCM_FILE } from "../constants/communicationEnums.js";

export function runScmCode(code, onOutput, onErr, onHalt) {
  return send(
    { handler: SCHEME, type: RUN_SCM_CODE, code },
    onOutput,
    onErr,
    onHalt
  );
}

export function runScmFile(location, onOutput, onErr, onHalt) {
  return send(
    { handler: SCHEME, type: RUN_SCM_FILE, location },
    onOutput,
    onErr,
    onHalt
  );
}
