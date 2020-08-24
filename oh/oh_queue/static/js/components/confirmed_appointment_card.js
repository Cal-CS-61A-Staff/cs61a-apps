function ConfirmedAppointmentCard({ appointment, signup, locations, assignments })  {
    const assignmentName = signup.assignment_id && assignments[signup.assignment_id].name;
    const questionName = signup.question ? " Question " + signup.question : "";

    const questionBlock = assignmentName && <React.Fragment>have asked for help with <b>{assignmentName + questionName}</b>, and</React.Fragment>;
    const helperBlock = appointment.helper && <React.Fragment>by <b>{appointment.helper.name}</b>, </React.Fragment>;

    const content = (
        <React.Fragment>
            Your appointment is at <b>{locations[appointment.location_id].name}</b>.
            You {questionBlock} will be helped {helperBlock} in a group of <b>{Math.max(appointment.capacity, appointment.signups.length)}</b>.
        </React.Fragment>
    );

    const [modalOpen, setModalOpen] = React.useState(false);

    const history = ReactRouterDOM.useHistory();

    const handleClick = (e) => {
        e.preventDefault();
        if (appointment.status === "active") {
            history.push("/appointments/" + appointment.id);
        } else {
            setModalOpen(true);
        }
    };

    const style = {};

    if (appointment.status === "active") {
        style.borderLeft = "5px solid #337ab7";
    }

    return (
        <React.Fragment>
            <div className="panel panel-default" onClick={handleClick} style={style}>
                <ul className="list-group">
                    <a href="#" className="list-group-item">
                        {appointment.status === "active" && <span className="badge badge-primary">Click To Enter</span>}
                        <h4 className="list-group-item-heading appointment-card-heading">
                            {formatAppointmentDate(appointment)}
                        </h4>
                        <div className="appointment-card-subheading">
                            {formatAppointmentDuration(appointment)}
                        </div>
                        {content}
                    </a>
                </ul>
            </div>
            <AppointmentOverlay
                assignments={assignments}
                appointment={appointment.id}
                signup={signup}
                isOpen={modalOpen}
                onSubmit={() => setModalOpen(false)}
            />
        </React.Fragment>
    )
}
