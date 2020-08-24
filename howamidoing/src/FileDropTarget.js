import React from "react";

import "./FileDropTarget.css";

export default function FileDropTarget({ onFileSelect, children }) {
    const highlight = (elem) => {
        elem.setAttribute("hover", "true");
    };

    const unHighlight = (elem) => {
        elem.setAttribute("hover", "false");
    };

    const processFilesUploaded = (files) => {
        const file = files[0];
        const reader = new FileReader();
        reader.readAsText(file);
        reader.onload = () => onFileSelect(reader.result);
    };

    const handleDragEnter = (e) => {
        e.preventDefault();
        e.stopPropagation();

        highlight(e.currentTarget);
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        e.stopPropagation();
        highlight(e.currentTarget);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        e.stopPropagation();

        unHighlight(e.currentTarget);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();

        unHighlight(e.currentTarget);

        const dt = e.dataTransfer;
        const { files } = dt;
        processFilesUploaded(files);
    };

    const handleFileUpload = (e) => {
        processFilesUploaded(e.target.files);
    };

    return (
        <div className="FileDropTarget">
            <div
                className="FileDropTargetBox"
                onDragEnter={handleDragEnter}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                <span className="centeredTextHolder">
                    {children}
                </span>
            </div>
            <label className="fileUploadButton">
                <div>
                    <span className="centeredTextHolder">Or click here to upload them manually</span>
                </div>
                <input
                    style={{ display: "none" }}
                    type="file"
                    onChange={handleFileUpload}
                />
            </label>
        </div>

    );
}
