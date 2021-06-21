import React, { Component } from "react";
import $ from "jquery";

import RegradeHandlerModal from "./RegradeHandlerModal.js";

class RegradeRequest extends Component {
  constructor(props) {
    super(props);
    this.cols = ["Email", "Assignment", "Status"];
    this.regradeModalRef = React.createRef();
  }

  handleRegradeModalClick = () => {
    $(this.regradeModalRef.current).modal();
  };

  getStatus() {
    if (this.props.request.status === "requested") {
      return <i className="fa fa-commenting-o"></i>;
    } else if (this.props.request.status === "denied") {
      return <i className="fa fa-times text-danger"></i>;
    } else if (this.props.request.status === "needs followup") {
      return <i className="fa fa-clock-o"></i>;
    } else {
      return <i className="fa fa-check text-success"></i>;
    }
  }

  render() {
    // eslint-disable-next-line react/no-array-index-key
    return (
      <tr
        key={`${this.props.request.assignment}/${this.props.request.backup_id}`}
      >
        {this.cols.map((x) => (
          <td key={x}>
            {x.toLowerCase() === "status"
              ? this.getStatus()
              : this.props.request[x.toLowerCase()]}
          </td>
        ))}
        <td>
          <div className="collapse show">
            <a
              href="#"
              onClick={this.handleRegradeModalClick}
              style={{ marginLeft: "10px" }}
            >
              <i className="fa fa-external-link"></i>
            </a>
            <RegradeHandlerModal
              ref={this.regradeModalRef}
              request={this.props.request}
            />
          </div>
        </td>
      </tr>
    );
  }
}

export default RegradeRequest;
