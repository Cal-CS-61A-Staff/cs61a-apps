function UpdateAssignmentBox({state, group}: {state: State, group: Group}) {
    const {assignments} = state;

    let filteredAssignments = Object.values(assignments).filter((assignment) => assignment.visible).sort((a, b) => a.name.localeCompare(b.name));

    const [assignment, setAssignment] = React.useState(group.assignment_id);
    const [question, setQuestion] = React.useState(group.question);

    const handleSubmit = () => {
        app.makeRequest("update_group", {id: group.id, assignment_id: assignment, question});
    }

    return (
        <div className="request-form form-group form-group-lg">
            <div className="input-group">
                <SelectPicker options={filteredAssignments}
                              value={assignment}
                              onChange={e => setAssignment(parseInt(e.target.value))}
                              className="selectpicker form-control form-left"
                              data-live-search="true" data-size="8" data-width="60%"
                              data-style="btn-lg btn-default" id="assignment_id"
                              name="assignment_id" title="Assignment" required/>
                <input className="form-control form-right" type="text" id="question"
                       name="question" title="Question" placeholder="Question"
                       value={question} onChange={e => setQuestion(e.target.value)}
                />
            </div>
          {assignment !== group.assignment_id || question !== group.question ? (
              <button
                  onClick={handleSubmit}
                  className="description-button btn btn-default btn-lg btn-block"
              >
                  {" "}Update Assignment{" "}
              </button>
          ) : null}
        </div>
    );
}
