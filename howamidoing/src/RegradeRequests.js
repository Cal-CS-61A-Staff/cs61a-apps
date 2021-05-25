import React, { Component } from "react";
import $ from "jquery";

import RegradeHandlerModal from "./RegradeHandlerModal.js";

class RegradeRequests extends Component {
  constructor(props) {
    super(props);
    this.state = {
      requests: [],
    };
    this.cols = ["Email", "Assignment", "Status"];

    this.regradeModalRef = React.createRef();
  }

  componentDidMount() {
    return this.reloadData();
  }

  reloadData = async (target) => {
    var location = "./getRegradeRequests";
    if (this.props.getAll) {
      location += "?for=all";
    }
    var requests = await $.getJSON(location, { target });
    this.setState({ requests: requests });
  };

  handleRegradeModalClick = () => {
    $(this.regradeModalRef.current).modal();
  };

  getStatus(request) {
    if (request.status === "requested") {
      return <i className="fa fa-commenting-o"></i>;
    } else if (request.status === "denied") {
      return <i className="fa fa-times text-danger"></i>;
    } else if (request.status === "needs followup") {
      return <i className="fa fa-clock-o"></i>;
    } else {
      return <i className="fa fa-check text-success"></i>;
    }
  }

  render() {
    const unresolved = this.state.requests.filter(
      (request) => request.status === "requested"
    );
    const unresolvedRows = unresolved.map((request) => (
      // eslint-disable-next-line react/no-array-index-key
      <tr key={`${request.assignment}/${request.backup_id}`}>
        {this.cols.map((x) => (
          <td key={x}>
            {x.toLowerCase() === "status"
              ? this.getStatus(request)
              : request[x.toLowerCase()]}
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
            <RegradeHandlerModal ref={this.regradeModalRef} request={request} />
          </div>
        </td>
      </tr>
    ));

    const resolved = this.state.requests.filter(
      (request) => request.status !== "requested"
    );
    const resolvedRows = resolved.map((request) => (
      // eslint-disable-next-line react/no-array-index-key
      <tr key={`${request.assignment}/${request.backup_id}`}>
        {this.cols.map((x) => (
          <td key={x}>
            {x.toLowerCase() === "status"
              ? this.getStatus(request)
              : request[x.toLowerCase()]}
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
              request={request}
              resolved={true}
            />
          </div>
        </td>
      </tr>
    ));

    return (
      <table className="table table-hover">
        <thead>
          <tr>
            {this.cols.concat(["Handle"]).map((col) => (
              <th scope="col" key={col}>
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{unresolvedRows.concat(resolvedRows)}</tbody>
      </table>
    );
  }
}

export default RegradeRequests;
