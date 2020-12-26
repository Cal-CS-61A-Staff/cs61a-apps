import React from "react";
import { dialogWrap } from "../utils/dialogWrap.js";
import LinkCopier from "./LinkCopier.js";
import StaffLinkCopier from "./StaffLinkCopier.js";

function ShareDialog({ link, fileData }) {
  return (
    <div className="modalCol">
      <LinkCopier link={link}>
        Share the following link with course staff to let us access your code.
      </LinkCopier>
      <br />
      <StaffLinkCopier fileData={fileData} />
    </div>
  );
}

export default dialogWrap("Share", ShareDialog, "column");
