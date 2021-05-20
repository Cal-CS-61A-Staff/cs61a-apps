import { LARK } from "../../../common/languages";
import { send } from "../../../renderer/utils/communication.js";
import { RUN_LARK_CODE } from "../constants/communicationEnums.js";

// eslint-disable-next-line import/prefer-default-export
export function runLarkCode(code, onOutput, onErr, onHalt) {
  return send(
    { handler: LARK, type: RUN_LARK_CODE, code },
    onOutput,
    onErr,
    onHalt
  );
}
