import React from "react";

import {
    Histogram, BarSeries, withParentSize, XAxis, YAxis,
} from "@data-ui/histogram";


const ResponsiveHistogram = withParentSize(({ parentWidth, parentHeight, ...rest }) => (
    <Histogram
        width={parentWidth}
        height={parentHeight}
        {...rest}
    />
));

export default function ScoreHistogram({ students, bins, extractedData }) {
    return (
        <div style={{ height: "40vh" }}>
            { students.length === 0
                    || (
                        <ResponsiveHistogram
                            ariaLabel="Lab score histogram"
                            orientation="vertical"
                            cumulative={false}
                            normalized
                            valueAccessor={datum => datum}
                            binType="numeric"
                            binValues={bins}
                            renderTooltip={({ datum, color }) => (
                                <div>
                                    <strong style={{ color }}>
                                        {datum.bin0}
                                        {" "}
                                    to
                                        {" "}
                                        {datum.bin1}
                                    </strong>
                                    <div>
                                        <strong>count </strong>
                                        {datum.count}
                                    </div>
                                    <div>
                                        <strong>cumulative </strong>
                                        {datum.cumulative}
                                    </div>
                                    <div>
                                        <strong>density </strong>
                                        {datum.density}
                                    </div>
                                </div>
                            )}
                        >
                            <BarSeries
                                animated
                                rawData={extractedData}
                            />
                            <XAxis />
                            <YAxis />
                        </ResponsiveHistogram>
                    )}
        </div>

    );
}
