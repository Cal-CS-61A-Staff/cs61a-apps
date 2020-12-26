import { RUN_BLACK } from "../constants/communicationEnums.js";
import { sendNoInteract } from "../../../renderer/utils/communication.js";
import { PYTHON } from "../../../common/languages.js";

export default async function format(code) {
  try {
    const out = await sendNoInteract({
      handler: PYTHON,
      type: RUN_BLACK,
      code,
    });
    return { success: true, code: out.substr(0, out.length - 1) };
  } catch (e) {
    return { success: false, error: e.message };
  }
}
