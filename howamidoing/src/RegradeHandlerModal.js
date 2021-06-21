import React, { Component } from "react";
import $ from "jquery";

export default React.forwardRef((props, ref) => {
  class RegradeHandlerModal extends Component {
    constructor(props) {
      super(props);
      this.state = {
        resolution: "Granted",
        reason: "",
      };
    }

    onChangeSelect = (e) => {
      this.setState({
        resolution: e.target.value,
      });
    };

    onChangeReason = (e) => {
      this.setState({
        reason: e.target.value,
      });
    };

    onClickSubmit = () => {
      const data = {
        email: props.request.email,
        assignment: props.request.assignment,
        backup_id: props.request.backup_id,
        resolution: this.state.resolution,
        reason: this.state.reason,
        email_preview: this.getEmailPreview(),
      };

      $.ajax({
        url: "./resolveRegradeRequest",
        type: "POST",
        data: JSON.stringify(data),
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: ({ success }) => {
          window.location.reload();
        },
      });
    };

    getEmailPreview() {
      const two =
        this.state.resolution === "Granted"
          ? window.ACCEPT_MESSAGE
          : this.state.resolution === "Denied"
          ? window.REJECT_MESSAGE
          : window.NEEDS_FOLLOWUP_MESSAGE;
      const three = this.state.reason === "" ? "" : ` ${this.state.reason}`;

      return `Hi,\n\nYour regrade request for ${
        props.request.assignment
      } has been processed. ${two + three}\n\nSincerely,\n${
        window.COURSE_CODE
      } Course Staff`;
    }

    render() {
      return (
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
                <h5 className="modal-title">
                  {props.request.email}'s Regrade Request for{" "}
                  {props.request.assignment}
                </h5>
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
                  <input
                    type="hidden"
                    readOnly
                    className="form-control-plaintext"
                    name="email"
                    value={props.request.email}
                  />
                  <input
                    type="hidden"
                    readOnly
                    className="form-control-plaintext"
                    name="assignment"
                    value={props.request.assignment}
                  />
                  <input
                    type="hidden"
                    readOnly
                    className="form-control-plaintext"
                    name="backup_id"
                    value={props.request.backup_id}
                  />
                  <p>
                    <a
                      href={`https://okpy.org/admin/grading/${props.request.backup_id}`}
                    >
                      Okpy Backup
                    </a>
                  </p>
                  <p>
                    Description
                    <br />
                    {props.request.description}
                  </p>
                  <div className="form-group">
                    <label htmlFor="resolution">Conclusion</label>
                    <select
                      className="form-control"
                      name="resolution"
                      onChange={this.onChangeSelect}
                    >
                      <option>Granted</option>
                      <option>Needs Followup</option>
                      <option>Denied</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label htmlFor="reason">Add a reason</label>
                    <textarea
                      className="form-control"
                      name="reason"
                      rows="3"
                      onChange={this.onChangeReason}
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="email_preview">Email Preview</label>
                    <textarea
                      className="form-control"
                      readOnly
                      name="email_preview"
                      rows="10"
                      value={this.getEmailPreview()}
                    />
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="submit"
                  className="btn btn-success text-white"
                  style={{ marginLeft: "10px" }}
                  id="resolveRequestButton"
                  onClick={this.onClickSubmit}
                  data-dismiss="modal"
                >
                  Resolve Request
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
      );
    }
  }

  return <RegradeHandlerModal />;
});
