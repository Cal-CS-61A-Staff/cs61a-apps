function UpdateAssignmentBox({state, elem, onSubmit}: {state: State, elem: Group | Ticket, onSubmit: ({assignment_id: number, question: string}) => void }) {
    const {assignments} = state;

    let filteredAssignments = Object.values(assignments).filter((assignment) => assignment.visible).sort((a, b) => a.name.localeCompare(b.name));

    const [assignment_id, setAssignment] = React.useState(elem.assignment_id);
    const [question, setQuestion] = React.useState(elem.question);

    return (
        <div className="request-form form-group form-group-lg">
            <div className="input-group">
                <SelectPicker options={filteredAssignments}
                              value={assignment_id}
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
          {assignment_id !== elem.assignment_id || question !== elem.question ? (
              <button
                  onClick={onSubmit({assignment_id, question})}
                  className="description-button btn btn-default btn-lg btn-block"
              >
                  {" "}Update Assignment{" "}
              </button>
          ) : null}
        </div>
    );
}
