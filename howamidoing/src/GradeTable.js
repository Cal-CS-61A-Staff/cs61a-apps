/* eslint-disable react/no-array-index-key */
import React from "react";
import Topic from "./Topic.js";

export default function GradeTable(props) {
  const rows = props.schema.map((elem, index) => (
    <Topic
      schema={elem}
      data={props.data}
      rawData={props.rawData}
      planned={props.planned}
      plannedTotals={props.plannedTotals}
      indent={0}
      key={index}
      future={props.future}
      onFutureScoreChange={props.onFutureScoreChange}
      email={props.email}
      ta={props.ta}
    />
  ));

  const scoreHeader = props.future
    ? "Expected / Maximum Possible"
    : "Current / Maximum Possible";

  return (
    <table className="table table-hover">
      <thead>
        <tr>
          <th scope="col" style={{ width: "50%" }}>
            Assignment
          </th>
          <th scope="col" style={{ width: "25%" }}>
            {scoreHeader}
          </th>
          {window.ENABLE_REGRADES ? (
            <th scope="col" style={{ width: "10%" }}>
              Regrade
            </th>
          ) : (
            ""
          )}
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  );
}
