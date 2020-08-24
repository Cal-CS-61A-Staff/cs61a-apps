function ConfirmedAppointment({ mySignups, locations, assignments }) {
    let body;
    if (mySignups.length === 0) {
        body = <p>Choose a slot to schedule a visit to office hours! </p>;
    } else {
        const innerBody = mySignups.map(({ appointment, signup }) => (
                <ConfirmedAppointmentCard
                    appointment={appointment}
                    assignments={assignments}
                    signup={signup}
                    locations={locations}
                />
            )
        );
        body = (
            <div className="confirmed-appointment-container">
                {innerBody}
            </div>
        )
    }
    return (
        <div className="jumbotron">
            <div className="container">
                <h2> Your Appointments </h2>
                {body}
            </div>
        </div>
    )
}
