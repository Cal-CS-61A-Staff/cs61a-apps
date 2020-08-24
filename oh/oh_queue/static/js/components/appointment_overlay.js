function AppointmentOverlay({ staffMode, appointment, assignments, signup, onSubmit, isOpen }) {
    const [email, setEmail] = React.useState("");
    const [assignment, setAssignment] = React.useState("");
    const [question, setQuestion] = React.useState("");
    const [description, setDescription] = React.useState("");

    const root = React.useRef();

    React.useEffect(() => {
        if (signup) {
            setEmail(signup.user.email || "");
            setAssignment(signup.assignment_id || "");
            setQuestion(signup.question || "");
            setDescription(signup.description || "");
        } else {
            setEmail("");
            setAssignment("");
            setQuestion("");
            setDescription("");
        }
    }, [signup]);

    React.useEffect(() => {
        if (isOpen) {
            $(root.current).modal("show");
        } else {
            $(root.current).modal("hide");
        }
    }, [isOpen]);

    React.useEffect(() => {
        $(root.current).on("hide.bs.modal", onSubmit);
    }, []);

    const handleCancel = () => {
        app.makeRequest("unassign_appointment", signup.id);
        onSubmit();
    };

    const handleSubmit = () => {
        app.makeRequest(
        'assign_appointment', {
            appointment_id: appointment,
            assignment_id: parseInt(assignment),
            question: question,
            description: description,
            email: signup ? signup.user.email : email,
        });
        onSubmit();
    };

    return ReactDOM.createPortal(
        <div className="modal fade" ref={root} tabIndex="-1" role="dialog">
            <div className="modal-dialog" role="document">
                <div className="modal-content">
                    <div className="modal-header">
                        <button type="button" className="close" data-dismiss="modal"
                                aria-label="Close"><span aria-hidden="true">&times;</span></button>
                        <h4 className="modal-title">
                            {staffMode ?
                                "Create / Edit Appointment Signup" : "What do you need help with?"}
                        </h4>
                    </div>
                    <div className="modal-body">
                        {!staffMode && (
                            <p>
                                Leave fields blank if you aren't yet sure what you want to ask about.
                            </p>
                        )}
                        <SlotsForm
                            assignments={assignments}
                            email={email}
                            onEmailChange={setEmail}
                            selectedAssignment={assignment}
                            onSelectedAssignmentChange={setAssignment}
                            question={question}
                            onQuestionChange={setQuestion}
                            description={description}
                            onDescriptionChange={setDescription}
                            showEmail={staffMode && !signup}
                        />
                    </div>
                    <div className="modal-footer">
                        <button type="button" className="btn btn-default"
                                data-dismiss="modal">Close
                        </button>
                        {signup && (
                            <button
                                type="button"
                                className="btn btn-danger"
                                onClick={handleCancel}
                            >Cancel Appointment</button>
                        )}
                        <button
                            type="button"
                            className="btn btn-primary"
                            onClick={handleSubmit}
                        >Confirm</button>
                    </div>
                </div>
            </div>
        </div>,
        document.body,
    );
}
