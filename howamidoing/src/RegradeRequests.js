import React, { Component } from "react";
import $ from "jquery";

import RegradeRequest from "./RegradeRequest.js";

class RegradeRequests extends Component {
  constructor(props) {
    super(props);
    this.state = {
      requests: [],
    };
    this.cols = ["Email", "Assignment", "Status"];
  }

  componentDidMount() {
    return this.reloadData();
  }

  reloadData = async (target) => {
    var location = "./getRegradeRequests";
    var requests = await $.getJSON(location, { target });
    this.setState({ requests: requests });
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
    const unresolvedRows = unresolved.map(
      (request) =>
        // eslint-disable-next-line react/no-array-index-key
        <RegradeRequest request={request} />
    );

    const resolved = this.state.requests.filter(
      (request) => request.status !== "requested"
    );
    const resolvedRows = resolved.map(
      (request) =>
        // eslint-disable-next-line react/no-array-index-key
        <RegradeRequest request={request} />
    );

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
