import SettingsDialog from "../renderer/components/SettingsDialog.js";
import { loadDialog } from "../renderer/utils/dialogWrap.js";
import { sendAndExit } from "./webBackend.js";

export default function showSettingsDialog(key, title, content) {
  function handleClose() {
    sendAndExit(key, { success: true });
  }

  loadDialog(SettingsDialog, { title, content, onClose: handleClose });
}
