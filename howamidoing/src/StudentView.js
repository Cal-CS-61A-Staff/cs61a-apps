/* eslint-disable no-param-reassign,dot-notation */
import React, { Component } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.min.js";

import "./StudentView.css";

import GradeTable from "./GradeTable.js";
import GradePlanner from "./GradePlanner.js";
import FutureCheckBox from "./FutureCheckBox.js";
import computeTotals from "./computeTotals.js";

import { getAssignmentLookup, getAssignments } from "./loadAssignments.js";

let ASSIGNMENTS = [];

let LOOKUP = {};

let setSchema;

const initialize = (header, scores) => {
    ({ setSchema } = window);
    setSchema(header, scores);
    LOOKUP = getAssignmentLookup();
    ASSIGNMENTS = getAssignments();
}

export const extend = (scores, lookup) => {
    const out = JSON.parse(JSON.stringify(scores));
    for (const key of Object.keys(lookup)) {
        if (out[key] === undefined) {
            out[key] = NaN;
        }
    }
    return out;
}

class StudentView extends Component {
    constructor(props) {
        super(props);

        const scores = {};
        initialize(props.header, props.data);

        for (let i = 0; i !== props.header.length; ++i) {
            if (LOOKUP[props.header[i]]) {
                scores[props.header[i]] = props.data[i];
            }
        }

        this.state = {
            scores,
            plannedScores: extend(scores, LOOKUP),
            future: false,
        };
    }

    handleFutureCheckboxChange = () => {
        this.setState(state => ({ future: !state.future, plannedScores: extend(state.scores) }));
    };

    handleFutureScoreChange = (name, newScore) => {
        this.state.plannedScores[name] = newScore === "" ? NaN : newScore;
        this.forceUpdate(); // sorry!
    };

    recursivelyMaximize = (topic, plannedScores) => {
        if (topic.isTopic) {
            for (const child of topic.children) {
                this.recursivelyMaximize(child, plannedScores);
            }
        } else if (topic.name !== "Final" && Number.isNaN(plannedScores[topic.name])) {
            plannedScores[topic.name] = topic.maxScore;
        }
    };

    handleSetCourseworkToMax = () => {
        this.recursivelyMaximize(ASSIGNMENTS[0], this.state.plannedScores);
        this.forceUpdate();
    };

    handleSetParticipationToMax = () => {
        for (const assignment of ASSIGNMENTS) {
            this.recursivelyMaximize(assignment, this.state.plannedScores);
        }
        this.forceUpdate();
    };

    render() {
        const scores = extend(this.state.scores, LOOKUP);

        if (this.state.future) {
            for (const elem of Object.values(LOOKUP)) {
                if (elem.default) {
                    scores[elem.name] = NaN;
                }
            }
        }

        const totals = computeTotals(ASSIGNMENTS, scores, this.state.future);
        const plannedTotals = computeTotals(
            ASSIGNMENTS, this.state.plannedScores, this.state.future,
        );

        const warning = window.WARNING
            // eslint-disable-next-line react/no-danger
            && <div className="alert alert-danger" dangerouslySetInnerHTML={{ __html: window.WARNING }} />;

        return (
            <>
                {warning}
                {window.ENABLE_PLANNING
                    && (
                        <FutureCheckBox
                            onChange={this.handleFutureCheckboxChange}
                            checked={this.state.future}
                        />
                    )
                }
                <br />
                {this.state.future && (
                    <GradePlanner
                        data={plannedTotals}
                        onSetCourseworkToMax={this.handleSetCourseworkToMax}
                        onSetParticipationToMax={this.handleSetParticipationToMax}
                    />
                )}
                <GradeTable
                    schema={ASSIGNMENTS}
                    data={totals}
                    planned={this.state.plannedScores}
                    plannedTotals={plannedTotals}
                    future={this.state.future}
                    onFutureScoreChange={this.handleFutureScoreChange}
                />
            </>
        );
    }
}

export default StudentView;
