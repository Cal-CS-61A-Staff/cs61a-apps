function SlotsForm({
                       assignments, showEmail,
                       email, onEmailChange,
                       selectedAssignment, onSelectedAssignmentChange,
                       question, onQuestionChange,
                       description, onDescriptionChange
                   }) {
    return (
        <form class="slots-form">
            <div className="form-group form-group-lg">
                {showEmail && (
                    <React.Fragment>
                        <input className="form-control" type="text"
                               name="email" title="Student Email" placeholder="somestudent@berkeley.edu"
                               value={email} onChange={e => onEmailChange(e.target.value)}
                               required/>
                        <br/>
                    </React.Fragment>
                )}
                <div className="input-group">
                    <SelectPicker options={assignments}
                                  value={selectedAssignment}
                                  onChange={e => onSelectedAssignmentChange(e.target.value)}
                                  className="selectpicker form-control form-left"
                                  data-live-search="true" data-size="8" data-width="60%"
                                  data-style="btn-lg btn-default"
                                  name="assignment_id" title="Assignment" required/>
                    <input className="form-control form-right" type="text"
                           name="question" title="Question" placeholder="Question"
                           value={question} onChange={e => onQuestionChange(e.target.value)}
                           required/>
                </div>
                <br/>
                <div className="input-group">
                    <textarea className="description-box" rows="5"
                              value={description}
                              onChange={e => onDescriptionChange(e.target.value)}
                              placeholder={"It would be helpful if you could describe your" +
                              " main points of confusion. For example, \"I don't understand how" +
                              " tree recursion works.\" \n\nCourse staff will read your" +
                              " descriptions before the section so that we can better help you."}
                              required
                    />
                </div>
            </div>
        </form>
    )
}
