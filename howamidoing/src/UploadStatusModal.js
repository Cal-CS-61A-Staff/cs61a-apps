import React from "react";

export default React.forwardRef(({ success }, ref) => (
    <div
        className="modal fade"
        tabIndex="-1"
        role="dialog"
        aria-hidden="true"
        ref={ref}
    >
        <div className="modal-dialog" role="document">
            <div className="modal-content">
                <div className="modal-header">
                    <h5 className="modal-title">Upload Status</h5>
                    <button type="button" className="close" data-dismiss="modal" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div className="modal-body">
                    {success ? "Upload succeeded!" : "Upload failed :( Refresh, and try again!" +
                        " If the issue persists, please contact the developers."}
                </div>
                <div className="modal-footer">
                    <button type="button" className="btn btn-secondary" data-dismiss="modal">
                        Close
                    </button>
                </div>
            </div>
        </div>
    </div>
));
