import { send } from "../../../renderer/utils/communication.js";
import { SQL } from "../../../common/languages.js";
import { RUN_SQL_CODE, RUN_SQL_FILE } from "../constants/communicationEnums.js";

export function runSQLCode(code, onOutput, onErr, onHalt) {
  return send(
    { handler: SQL, type: RUN_SQL_CODE, code },
    onOutput,
    onErr,
    onHalt
  );
}

export function runSQLFile(location, onOutput, onErr, onHalt) {
  return send(
    { handler: SQL, type: RUN_SQL_FILE, location },
    onOutput,
    onErr,
    onHalt
  );
}
