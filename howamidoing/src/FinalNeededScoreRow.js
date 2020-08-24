import React from "react";

export default function FinalNeededScoreRow(props) {
    return (
        <tr>
            <th scope="row">{props.grade}</th>
            <td>{props.score}</td>
        </tr>
    );
}
