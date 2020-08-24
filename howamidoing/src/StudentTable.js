import React from "react";

export default function StudentTable({ students, onLogin }) {
    const cols = ["Name", "Email", "SID", "Score"];
    const studentRows = students.map((student, i) => (
        // eslint-disable-next-line react/no-array-index-key
        <tr key={i}>
            {cols.map(x => <td key={x}>{student[x]}</td>)}
            <td><button type="button" onClick={() => onLogin(student.Email)}>Enter</button></td>
        </tr>
    ));

    return (
        <table className="table table-hover">
            <thead>
                <tr>
                    {cols.map(col => <th scope="col" key={col}>{col}</th>)}
                    <th>Login As</th>
                </tr>
            </thead>
            <tbody>
                { studentRows }
            </tbody>
        </table>
    );
}
