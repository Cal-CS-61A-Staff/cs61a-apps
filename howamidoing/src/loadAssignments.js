export const getAssignments = () => {
    const { createAssignments } = window;
    return createAssignments();
};

export const getAssignmentLookup = () => {
    const ASSIGNMENTS = getAssignments();
    const lookup = {};

    const populateLookup = (assignment) => {
        lookup[assignment.name] = assignment;
        if (assignment.isTopic) {
            for (const child of assignment.children) {
                populateLookup(child);
            }
        }
    };

    for (const assignment of ASSIGNMENTS) {
        populateLookup(assignment);
    }
    return lookup;
};
