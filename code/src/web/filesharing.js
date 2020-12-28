import $ from "jquery";
import { randomString } from "../common/misc";

import { sendAndExit } from "./webBackend.js";
import ShareDialog from "../renderer/components/ShareDialog.js";
import { loadDialog } from "../renderer/utils/dialogWrap.js";

export default async function showShareDialog(key, name, contents, shareRef) {
  if (!shareRef) {
    // eslint-disable-next-line no-param-reassign
    shareRef = randomString();
  }
  const fileData = { fileName: name, fileContent: contents, shareRef };
  const link = await $.post("./api/share", fileData);
  loadDialog(ShareDialog, {
    onClose: () => {
      sendAndExit(key, { success: true, shareRef });
    },
    fileData,
    link,
  });
}
