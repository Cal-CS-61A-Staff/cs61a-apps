import ErrorDialog from "../renderer/components/ErrorDialog.js";
import { loadDialog } from "../renderer/utils/dialogWrap.js";
import { sendAndExit } from "./webBackend.js";

export default function showErrorDialog(key, title, content) {
  function handleClose() {
    sendAndExit(key, { success: true });
  }

  loadDialog(ErrorDialog, { title, content, onClose: handleClose });
}
