import React from "react";
import FinalNeededScoreTable from "./FinalNeededScoreTable.js";

export default function GradePlanner(props) {
    const { canDisplayFinalGrades, computeNeededFinalScore, participationProvided } = window;
    const { data: scores } = props;
    if (!canDisplayFinalGrades(scores)) {
        return (
            <>
                <div className="card">
                    <h5 className="card-header">Grade Planning</h5>
                    <div className="card-body">
                        <h5 className="card-title">Insufficient Data</h5>
                        <p className="card-text">
                            You need to specify your expected assignment scores (except for the
                            final!) in the below table to enable grade planning.
                        </p>
                        <p>
                            Or click the button to set them all to the maximum (including extra
                            credit)!
                        </p>
                        <button
                            className="btn btn-primary"
                            type="button"
                            onClick={props.onSetCourseworkToMax}
                        >
                            Set all unknown non-final scores to maximum
                        </button>
                    </div>
                </div>
                <br />
            </>
        );
    }

    const [grades, needed] = computeNeededFinalScore(scores);

    if (!participationProvided(scores)) {
        return (
            <>
                <div className="card">
                    <h5 className="card-header">Grade Planning</h5>
                    <div className="card-body">
                        <FinalNeededScoreTable
                            grades={grades}
                            needed={needed}
                        />
                        <p className="card-text">
                            To take exam recovery points into account, specify
                            an estimate of your participation credits. Or click the button to set
                            them all to the maximum!
                        </p>
                        <button
                            className="btn btn-primary"
                            type="button"
                            onClick={props.onSetParticipationToMax}
                        >
                            Set all unknown participation credits to maximum
                        </button>
                    </div>
                </div>
                <br />
            </>
        );
    } else {
        return (
            <>
                <div className="card">
                    <h5 className="card-header">Grade Planning</h5>
                    <div className="card-body">
                        <FinalNeededScoreTable
                            grades={grades}
                            needed={needed}
                        />
                    </div>
                </div>
                <br />
            </>
        );
    }
}
