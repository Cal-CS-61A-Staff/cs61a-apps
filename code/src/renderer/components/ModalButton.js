import React from "react";

export default function ModalButton({ children, buttonText, onClick }) {
  return (
    <div className="ModalButton">
      {children}
      <button className="fileDownloadBtn" type="button" onClick={onClick}>
        {buttonText}
      </button>
    </div>
  );
}
