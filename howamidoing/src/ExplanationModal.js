import React from "react";
import "katex/dist/katex.css";
import Latex from "react-latex";

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
          <h5 className="modal-title">Grade Explanation</h5>
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
            <Latex displayMode>{window.EXPLANATION}</Latex>
          </div>
        </div>
        <div className="modal-footer">
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
