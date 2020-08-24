import React from "react";
import BinSelector from "./BinSelector.js";

export default function BinSelectors({ bins, toggled, onToggle }) {
    const binSelectors = bins.map(
        (bin, i) => (
            <BinSelector
                key={bin}
                toggled={toggled[i]}
                onToggle={() => onToggle(i)}
            >
                {bin}
            </BinSelector>
        ),
    );

    return (
        <>
            <div>
                Show students with scores:
            </div>
            <div className="btn-group" role="group" aria-label="Basic example">
                {binSelectors}
            </div>
        </>
    );
}
