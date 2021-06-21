import React, { Component } from "react";
import $ from "jquery";

export default React.forwardRef((props, ref) => {
  class RegradeRequestModal extends Component {
    constructor(props) {
      super(props);

      this.state = {
        backup_id: "",
        description: "",
        submittable: false,
      };
    }

    verifySubmittable(backup_id, description) {
      this.setState({
        submittable: backup_id.length === 6 && description !== "",
      });
    }

    onChangeID = (e) => {
      this.setState({
        backup_id: e.target.value,
      });

      this.verifySubmittable(e.target.value, this.state.description);
    };

    onChangeDesc = (e) => {
      this.setState({
        description: e.target.value,
      });

      this.verifySubmittable(this.state.backup_id, e.target.value);
    };

    onClickSubmit = () => {
      const data = {
        email: props.email,
        assignment: props.assignment,
        backup_id: this.state.backup_id,
        description: this.state.description,
        ta: props.ta,
      };

      $.ajax({
        url: "./submitRegradeRequest",
        type: "POST",
        data: JSON.stringify(data),
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: ({ success }) => {
          if (success) {
            window.alert("Your request was submitted successfully!");
          } else {
            window.alert(
              "Your request was unsuccessful. Please wait a while and then try submitting again!"
            );
          }
        },
      });
    };

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
                  Request Regrade for {props.assignment}
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
                    value={props.email}
                  />
                  <input
                    type="hidden"
                    readOnly
                    className="form-control-plaintext"
                    name="assignment"
                    value={props.assignment}
                  />
                  <div className="form-group">
                    <label htmlFor="backup_id">Okpy Backup ID</label>
                    <input
                      type="text"
                      className="form-control"
                      name="backup_id"
                      aria-describedby="backupHelp"
                      placeholder="required; 6 characters"
                      maxLength="6"
                      onChange={this.onChangeID}
                    />
                    <small id="backupHelp" className="form-text text-muted">
                      https://okpy.org/cal/cs61a/&lt;semester&gt;/&lt;assignment&gt;/&lt;BACKUP_ID&gt;
                    </small>
                  </div>
                  <div className="form-group">
                    <label htmlFor="description">Describe your request</label>
                    <textarea
                      className="form-control"
                      name="description"
                      rows="3"
                      placeholder="required"
                      onChange={this.onChangeDesc}
                    />
                  </div>
                  <input
                    type="hidden"
                    readOnly
                    className="form-control-plaintext"
                    name="ta"
                    value={props.ta}
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="submit"
                  className="btn btn-success text-white"
                  style={{ marginLeft: "10px" }}
                  onClick={this.onClickSubmit}
                  id="submitRequestButton"
                  disabled={!this.state.submittable}
                  data-dismiss="modal"
                >
                  Submit Request
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
  return <RegradeRequestModal />;
});
