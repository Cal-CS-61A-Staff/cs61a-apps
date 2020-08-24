import React from "react";

export default function BinSelector({ children, toggled, onToggle }) {
    const className = toggled ? "btn btn-secondary" : "btn btn-outline-secondary";

    return (
        <button type="button" className={className} onClick={onToggle}>
            {children}
        </button>
    );
}
