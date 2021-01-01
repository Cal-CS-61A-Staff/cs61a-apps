import { FORMAT } from "../constants/communicationEnums.js";
import { sendNoInteract } from "../../../renderer/utils/communication.js";
import { SCHEME } from "../../../common/languages.js";

export default async function format(code) {
  try {
    return await sendNoInteract({
      handler: SCHEME,
      type: FORMAT,
      code,
    });
  } catch (e) {
    return { success: false, error: e.message };
  }
}
