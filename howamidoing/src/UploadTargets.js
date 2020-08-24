import React, { useState, useRef } from "react";
import $ from "jquery";

import FileDropTarget from "./FileDropTarget.js";
import UploadStatusModal from "./UploadStatusModal.js";

import "./UploadTargets.css";

export default function UploadTargets() {
    const [success, setSuccess] = useState(false);
    const modalRef = useRef();

    const upload = path => (data) => {
        $.post(path, { data }).done((ret) => {
            setSuccess(ret);
            $(modalRef.current).modal();
        }).catch(() => {
            setSuccess(false);
            $(modalRef.current).modal();
        });
    };
    return (
        <div className="UploadTargets">
            <FileDropTarget onFileSelect={upload("/setConfig")}>
                Drop config.js files here
            </FileDropTarget>
            <FileDropTarget onFileSelect={upload("/setGrades")}>
                Drop grades.csv files here
            </FileDropTarget>
            <UploadStatusModal ref={modalRef} success={success} />
        </div>
    );
}
