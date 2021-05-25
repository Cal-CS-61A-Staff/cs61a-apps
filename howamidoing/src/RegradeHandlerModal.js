import React, { Component } from "react";
import $ from "jquery";

export default React.forwardRef((props, ref) => {
  class RegradeHandlerModal extends Component {

  constructor(props) {
    super(props);
    this.state = {
      resolution: "Granted",
      reason: ""
    }
  }

  onChangeSelect = e => {
    this.setState({
      resolution: e.target.value,
    })
  }

  onChangeReason = e => {
    this.setState({
      reason: e.target.value,
    })
  }

  getEmailPreview() {
    const two = this.state.resolution === "Granted" ? window.ACCEPT_MESSAGE : window.REJECT_MESSAGE
    const three = this.state.reason === "" ? "" : ` ${this.state.reason}`

    return `Hi,\n\nYour regrade request for ${props.request.assignment} has been processed. ${two + three}\n\nSincerely,\n${window.COURSE_CODE} Course Staff`
  }

  render() {
    return <div
    className="modal fade"
    tabIndex="-1"
    role="dialog"
    aria-hidden="true"
    ref={ref}
  >
    <div className="modal-dialog modal-lg" role="document">
      <div className="modal-content">
        <div className="modal-header">
          <h5 className="modal-title">{props.request.email}'s Regrade Request for {props.request.assignment}</h5>
          <button
            type="button"
            className="close"
            data-dismiss="modal"
            aria-label="Close"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <form action="./resolveRegradeRequest" method="post">
        <div className="modal-body">
          <div style={{ width: "100%", overflowX: "auto" }}>
            <input type="hidden" readonly class="form-control-plaintext" name="email" value={props.request.email} />
            <input type="hidden" readonly class="form-control-plaintext" name="assignment" value={props.request.assignment} />
            <input type="hidden" readonly class="form-control-plaintext" name="backup_id" value={props.request.backup_id} />
            <p><a href={`https://okpy.org/admin/grading/${props.request.backup_id}`}>Okpy Backup</a></p>
            <p>Description<br />{props.request.description}</p>
            <div class="form-group">
              <label for="resolution">Conclusion</label>
              <select class="form-control" name="resolution" onChange={this.onChangeSelect}>
                <option>Granted</option>
                <option>Denied</option>
              </select>
            </div>
            <div class="form-group">
              <label for="reason">Add a reason</label>
              <textarea class="form-control" name="reason" rows="3" onChange={this.onChangeReason} />
            </div>
            <div class="form-group">
              <label for="email_preview">Email Preview</label>
              <textarea class="form-control" readonly name="email_preview" rows="10" value={this.getEmailPreview()} />
            </div>
          </div>
        </div>
        <div className="modal-footer">
          <button
            type="submit"
            className="btn btn-success text-white"
            style={{ marginLeft: "10px" }}
            id="resolveRequestButton"
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
        </form>
      </div>
    </div>
  </div>
  }
  }

  return <RegradeHandlerModal />
});
