let header;
let scores;

export function setSchema(_header, _scores) {
    header = _header;
    scores = _scores;
}

window.setSchema = setSchema;

export function sum(array) {
    return array.reduce((a, b) => a + b, 0);
}

/* eslint-disable no-param-reassign,dot-notation */
export function range(a, b) {
    if (!b) {
        b = a;
        a = 0;
    }
    const out = [];
    for (let i = a; i !== b; ++i) {
        out.push(i);
    }
    return out;
}

export function Topic(name, children, cappedScore = Infinity, customCalculator) {
    let future = true;
    const maxChildScores = [];
    for (const child of children) {
        if (!child.future && !child.hidden) {
            future = false;
            maxChildScores.push(child.maxScore);
        }
    }
    const maxFutureChildScores = [];
    for (const child of children) {
        maxFutureChildScores.push(child.futureMaxScore);
    }

    let maxScore;
    let futureMaxScore;

    if (customCalculator) {
        maxScore = Math.min(cappedScore, customCalculator(maxChildScores));
        futureMaxScore = Math.min(cappedScore, customCalculator(maxFutureChildScores));
    } else {
        maxScore = Math.min(cappedScore, maxChildScores.reduce((a, b) => a + b, 0));
        futureMaxScore = Math.min(cappedScore, maxFutureChildScores.reduce((a, b) => a + b, 0));
    }

    if (!maxScore) {
        maxScore = cappedScore;
    }
    if (!futureMaxScore) {
        futureMaxScore = cappedScore;
    }

    return {
        isTopic: true,
        name,
        children,
        maxScore,
        futureMaxScore,
        customCalculator,
        future,
    };
}

export function Assignment(name, maxScore) {
    return {
        isTopic: false,
        name,
        maxScore,
        futureMaxScore: maxScore,
        future: !header.includes(name),
    };
}

export function Always(elem) {
    elem.future = false;
    return elem;
}

export function Hidden(elem) {
    elem.hidden = true;
    return elem;
}

export function OnlyDefault(elem) {
    elem.default = true;
    return elem;
}

export function NoScore(elem) {
    elem.noScore = true;
    return elem;
}

export function LockedChildren(elem) {
    elem.lockedChildren = true;
    return elem;
}

export function BooleanValued(elem) {
    elem.booleanValued = true;
    return elem;
}
