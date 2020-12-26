import React, { Component } from "react";

export default class UploadFileSelector extends Component {
  handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();

    this.highlight(e.currentTarget);
  };

  handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    this.highlight(e.currentTarget);
  };

  handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();

    this.unHighlight(e.currentTarget);
  };

  handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();

    this.unHighlight(e.currentTarget);

    const dt = e.dataTransfer;
    const { files } = dt;
    this.processFilesUploaded(files);
  };

  handleFileUpload = (e) => {
    this.processFilesUploaded(e.target.files);
  };

  highlight = (elem) => {
    // eslint-disable-next-line no-param-reassign
    elem.style.borderColor = "yellow";
  };

  unHighlight = (elem) => {
    // eslint-disable-next-line no-param-reassign
    elem.style.borderColor = "white";
  };

  processFilesUploaded(files) {
    const file = files[0];
    const reader = new FileReader();
    reader.readAsText(file);
    reader.onload = () => {
      this.props.onFileSelect({
        name: file.name ? file.name : "untitled",
        location: null,
        content: reader.result,
        shareRef: null,
      });
    };
  }

  render() {
    return (
      <div className="modalCol localFileSelector">
        <div className="browserFileSelector">Upload Files</div>
        <div
          className="fileDropTarget"
          onDragEnter={this.handleDragEnter}
          onDragOver={this.handleDragOver}
          onDragLeave={this.handleDragLeave}
          onDrop={this.handleDrop}
        >
          <span className="centeredTextHolder">
            {" "}
            Drag files here to upload.{" "}
          </span>
        </div>
        <label>
          <div className="fileUploadButton">
            <span className="centeredTextHolder">
              {" "}
              Or click here to select files.{" "}
            </span>
          </div>
          <input
            style={{ display: "none" }}
            type="file"
            onChange={this.handleFileUpload}
          />
        </label>
      </div>
    );
  }
}
