import React from "react";

export default function FutureCheckBox(props) {
    return (
        <div className="custom-control custom-checkbox">
            <input type="checkbox" className="custom-control-input" id="futureCheckBox" checked={props.checked} onChange={props.onChange} />
            <label className="custom-control-label" htmlFor="futureCheckBox">
                Show unreleased / ungraded assignments and enable grade planning.
            </label>
        </div>
    );
}
