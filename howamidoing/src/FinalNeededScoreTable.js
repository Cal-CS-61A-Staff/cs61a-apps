import React from "react";
import FinalNeededScoreRow from "./FinalNeededScoreRow.js";

export default function FinalNeededScoreTable(props) {
    const rows = [];
    for (let i = 0; i !== props.needed.length; ++i) {
        rows.push(<FinalNeededScoreRow key={i} grade={props.grades[i]} score={props.needed[i]} />);
    }

    return (
        <table className="table">
            <thead>
                <tr>
                    <th scope="col">Grade</th>
                    <th scope="col">Minimum score needed on final</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    );
}
