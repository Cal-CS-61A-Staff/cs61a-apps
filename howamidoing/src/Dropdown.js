import React from "react";

import "./Dropdown.css";
import Select2 from "react-select2-wrapper";

export default function MyDropdown({ value, children, onChange }) {
    return (
        <div className="Dropdown">
            <Select2
                style={{ width: 300 }}
                value={value}
                onSelect={e => onChange(children.indexOf(e.target.value))}
                data={children}
            />
        </div>
    );
}
