import React from "react";
import $ from "jquery";
import buildExportURI from "./scoreExporter.js";

export default React.forwardRef((props, ref) => (
  <div
    className="modal fade"
    tabIndex="-1"
    role="dialog"
    aria-hidden="true"
    ref={ref}
  >
    <div className="modal-dialog modal-lg" role="document">
      <div className="modal-content">
        <div className="modal-header">
          <h5 className="modal-title">Export Instructions</h5>
          <button
            type="button"
            className="close"
            data-dismiss="modal"
            aria-label="Close"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <div className="modal-body">
          <div style={{ width: "100%", overflowX: "auto" }}>
            <p>
              Make sure to push updated grades to Howamidoing before exporting!
            </p>
            {window.EXPORT_INSTRUCTIONS ? (
              <p
                dangerouslySetInnerHTML={{ __html: window.EXPORT_INSTRUCTIONS }}
              ></p>
            ) : (
              ""
            )}
          </div>
        </div>
        <div className="modal-footer">
          <button
            type="button"
            className="btn btn-success text-white"
            style={{ marginLeft: "10px" }}
            id="exportButton"
            onClick={(e) => {
              e.preventDefault();

              $("#exportButton").html("Building export...");
              $("#exportButton").prop("disabled", true);

              const link = document.createElement("a");
              link.download = "export.csv";
              link.href = buildExportURI();

              $("#exportButton").prop("disabled", false);
              $("#exportButton").html("Export Scores");

              link.click();
            }}
          >
            Export Scores
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            data-dismiss="modal"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
));
