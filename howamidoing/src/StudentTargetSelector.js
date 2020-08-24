import React, { useState } from "react";
import Select2 from "react-select2-wrapper";
import $ from "jquery";

export default function StudentTargetSelector({ onSubmit, students }) {
    const [selected, setSelected] = useState(null);

    return (
        <form onSubmit={(e) => {
            e.preventDefault();
            onSubmit(selected);
        }}
        >
            <div className="form-group">
                <label htmlFor="inputEmail">Enter target student email address</label>
                <br />
                <Select2
                    style={{ width: "100%" }}
                    value={selected}
                    onSelect={x => setSelected($(x.target).val())}
                    data={students}
                />
            </div>
            <button type="submit" className="btn btn-primary" style={{ marginRight: "10px" }}>Submit</button>
            <a className="btn btn-success text-white" href="/histogram"> View Histogram </a>
        </form>
    );
}
