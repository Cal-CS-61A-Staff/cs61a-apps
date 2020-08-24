import {
    Assignment, range, Topic,
} from "./elements.js";

const BINS = [300, 285, 270, 250, 225, 205, 195, 185, 175, 170, 165, 160, 0];
const GRADES = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"];

export const COURSE_CODE = "61A";

export const WARNING = `Please note that these scores are tentative and serve only as a rough guideline for your performance in the class. Grades listed here do not guarantee that assignment grade or final grade; we reserve the right to change these grades in the event of any mitigating circumstances (e.g., cheating, another violation of course policy, etc.) or errors in grading. If you spot a possible issue with any of your grades OR any bugs with the Status Check, please let us know using by emailing us at: <a href="mailto:cs61a+sp20@berkeley.edu">cs61a+sp20@berkeley.edu</a></b>`;


export const EXPLANATION = String.raw`https://cs61a.org/articles/about.html#grading`;
export const EXPLANATION_IS_LINK = true;

export const ENABLE_PLANNING = true;

window.COURSE_CODE = COURSE_CODE;
window.createAssignments = createAssignments;
window.canDisplayFinalGrades = canDisplayFinalGrades;
window.computeNeededFinalScore = computeNeededFinalScore;
window.participationProvided = participationProvided;
window.WARNING = WARNING;
window.EXPLANATION = EXPLANATION;
window.ENABLE_PLANNING = ENABLE_PLANNING;
window.EXPLANATION_IS_LINK = true;

export function createAssignments() {
    return [
        Topic("Raw Score", [
            Topic("Exams", [
                Topic("Midterm 1", [
                    Assignment("Midterm 1 (Total)", 40),
                    Topic("Midterm 1 Recovery Points", [
                        Assignment("Midterm 2 (Total)", 40),
                        Assignment("Total Discussion Attendance (for midterm recovery)"),
                    ]),
                ]),
                Topic("Midterm 2", [
                    Assignment("Midterm 2 (Total)", 40),
                    Topic("Midterm 2 Recovery Points", [
                        Assignment("Midterm 2 (Total)", 40),
                        Assignment("Total Discussion Attendance (for midterm recovery)"),
                    ]),
                ]),
            ]),
            Topic("Homework", [
                ...range(1, 11).map(i => Assignment(`Homework ${i}`, 2)),
            ]),
            Topic("Projects", [
                Topic("Hog Project", [
                    Assignment("Hog (Total)", 23),
                    Assignment("Hog Checkpoint (Total)", 1),
                    Assignment("Hog (Composition)", 2),
                ]),
                Topic("Cats Project", [
                    Assignment("Cats (Total)", 18),
                    Assignment("Cats Checkpoint (Total)", 1),
                    Assignment("Cats (Composition)", 2),
                ]),
                Topic("Ants Project", [
                    Assignment("Ants (Total)", 30),
                    Assignment("Ants Checkpoint (Total)", 1),
                    Assignment("Ants (Composition)", 2),
                ]),
                Topic("Scheme Project", [
                    Assignment("Scheme (Total)", 28),
                    Assignment("Scheme Checkpoint (Total)", 1),
                ]),
            ]),
            Topic("Lab", [
                ...range(1, 13).filter(i => ![].includes(i)).map(i => Assignment(`Lab ${i} (Total)`, 1)),
            ], 10),
            Topic("Discussion", [
                ...range(1, 12).filter(i => ![].includes(i)).map(i => Assignment(`Discussion ${i} (Total)`, 1)),
            ], 5),
        ]),
        Topic("Total Discussion Attendance (for midterm recovery)", [
            ...range(1, 12).filter(i => ![8, 13].includes(i)).map(i => Assignment(`Discussion ${i} (Total)`, 1)),
        ], 10),
    ];
}

export function canDisplayFinalGrades(scores) {
    const {
        Homework, Projects, Lab, Discussion, "Midterm 1 (Total)": MT1, "Midterm 2 (Total)": MT2, "Midterm Recovery": Recovery,
    } = scores;
    return !Number.isNaN(Homework + Projects + MT1 + MT2 + Lab + Discussion);
}

export function computeNeededFinalScore(scores) {
    const {
        Homework, Projects, Lab, Discussion, "Midterm 1 (Total)": MT1, "Midterm 2 (Total)": MT2,
    } = scores;

    let { "Midterm Recovery": Recovery } = scores;
    if (!Recovery) {
        Recovery = 0;
    }

    const totalNonFinal = Homework
        + Projects
        + MT1
        + MT2
        + Recovery;
    //+ examRecover(MT1, Clobber, 40)
    //+ examRecover(MT2, Clobber, 50);

    const needed = [];
    const grades = [];

    for (const [bin, i] of BINS.map((val, index) => [val, index])) {
        const neededScore = Math.max(0, bin - totalNonFinal);
        if (neededScore <= 75) {
            needed.push(`${neededScore} / 75`);
            grades.push(GRADES[i]);
        }
        if (neededScore === 0) {
            break;
        }
    }

    return [grades, needed];
}

function examRecover(examScore, participation, maxExamScore, cap = 20) {
    const halfScore = maxExamScore / 2;
    const maxRecovery = Math.max(0, (halfScore - examScore) / 2);
    const recoveryRatio = Math.min(participation, cap) / cap;
    return maxRecovery * recoveryRatio;
}

export function participationProvided(scores) {
    const { "Participation Credits (for midterm recovery)": Participation } = scores;
    return !Number.isNaN(Participation);
}