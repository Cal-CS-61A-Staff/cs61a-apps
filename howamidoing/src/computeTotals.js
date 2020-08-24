/* eslint-disable no-param-reassign */
function parse(score) {
    if (Number.isNaN(parseFloat(score))) {
        return score;
    }
    return Number.parseFloat(score);
}

export default (assignments, scores, future) => {
    const totals = {};

    const computeTotals = (curr) => {
        if (totals[curr.name]) { // TODO: remove this kludge
            return totals[curr.name];
        }

        if (curr.future && !future) {
            return NaN;
        }

        if (!curr.isTopic) {
            totals[curr.name] = (scores[curr.name] !== undefined)
                ? parse(scores[curr.name]) : NaN;
            return totals[curr.name];
        }
        const childTotals = [];

        let out = 0;
        for (const child of curr.children.slice().reverse()) {
            if (child.future && !future) {
                continue;
            }
            const childTotal = computeTotals(child, totals);
            out += childTotal;
            childTotals.push(childTotal);
        }

        childTotals.reverse();
        if (curr.customCalculator) {
            out = curr.customCalculator(childTotals, future);
        }

        const limit = future ? curr.futureMaxScore : curr.maxScore;

        if (limit) {
            out = Math.min(out, limit);
        }

        totals[curr.name] = out;

        if (scores[curr.name] !== undefined
            && !Number.isNaN(Number.parseFloat(scores[curr.name]))) {
            totals[curr.name] = Number.parseFloat(scores[curr.name]);
            return totals[curr.name];
        }
        return out;
    };
    for (const assignment of assignments) {
        computeTotals(assignment);
    }

    return totals;
};
