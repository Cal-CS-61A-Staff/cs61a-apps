/* eslint-disable react/no-array-index-key */
import React from "react";
import Topic from "./Topic.js";

export default function GradeTable(props) {
    const rows = props.schema.map((elem, index) => (
        <Topic
            schema={elem}
            data={props.data}
            planned={props.planned}
            plannedTotals={props.plannedTotals}
            indent={0}
            key={index}
            future={props.future}
            onFutureScoreChange={props.onFutureScoreChange}
        />
    ));

    const scoreHeader = props.future ? "Expected / Maximum score eventually possible" :
        "Current / Maximum score possible so far";

    return (
        <table className="table table-hover">
            <thead>
                <tr>
                    <th scope="col" style={{ width: "50%" }}>Assignment</th>
                    <th scope="col" style={{ width: "25%" }}>{scoreHeader}</th>
                </tr>
            </thead>
            <tbody>
                { rows }
            </tbody>
        </table>
    );
}
