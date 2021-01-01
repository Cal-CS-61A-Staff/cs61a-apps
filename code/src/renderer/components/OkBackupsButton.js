import React from "react";
import ModalButton from "./ModalButton.js";
import { login } from "../utils/auth.js";
import { useAuthData } from "../utils/okUtils.js";

export default function OkBackupsButton({ onBackupsButtonClick }) {
  const { loggedOut } = useAuthData();

  const handleBackupsClick = async () => {
    if (loggedOut) {
      login();
    } else {
      onBackupsButtonClick();
    }
  };

  const okButtonText = `${loggedOut ? "Login" : "Click"} to view backups`;

  return (
    <ModalButton buttonText={okButtonText} onClick={handleBackupsClick}>
      <div className="LaunchScreenHeader">OKPy Backups</div>
    </ModalButton>
  );
}
