import { sendAndExit } from "./webBackend.js";
import { closeDialog, loadDialog } from "../renderer/utils/dialogWrap.js";
import { getAssignments } from "./filesystem.js";
import OkBackupsDialog from "../renderer/components/OkBackupsDialog.js";

// eslint-disable-next-line import/prefer-default-export
export async function showBackupsDialog(key) {
  function handleClose() {
    sendAndExit(key, { success: false });
  }

  function handleFileSelect(file) {
    closeDialog();
    sendAndExit(key, { success: true, file });
  }

  const assignments = await getAssignments();

  loadDialog(OkBackupsDialog, {
    assignments,
    onClose: handleClose,
    onFileSelect: handleFileSelect,
  });
}
