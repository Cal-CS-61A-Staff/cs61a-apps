function StaffUpcomingAppointments({ myAppointments, locations }) {
    let body;
    if (myAppointments.length === 0) {
        body = <p>Sign up for appointments below! </p>;
    } else {
        const innerBody = myAppointments.map(appointment => (
                <StaffUpcomingAppointmentCard
                    appointment={appointment}
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
