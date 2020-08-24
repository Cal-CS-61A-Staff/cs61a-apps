function MyAppointments({ state }) {
    const studentContent = getMySignups(state)
        .filter(({ appointment }) => appointment.status === "active" || isSoon(appointment))
        .map(({ appointment, signup }) => {
            const handleClick = appointment.status !== "pending" && (() => redirect(appointment.id));
            return (
                <ConfirmedAppointmentCard
                    assignments={state.assignments}
                    locations={state.locations}
                    appointment={appointment}
                    signup={signup}
                    onClick={handleClick}
                />
            )
        });

    const staffContent = getMyAppointmentsStaff(state)
        .filter(appointment => appointment.status === "active" || isSoon(appointment))
        .filter(({ status }) => status !== "resolved")
        .filter(({ signups }) => signups.length > 0)
        .sort((x, y) => (+!!y.helper - +!!x.helper) * 2 + appointmentTimeComparator(x, y))
        .map(appointment => {
            return (
                <StaffUpcomingAppointmentCard
                    appointment={appointment}
                    locations={state.locations}
                />
            )
        });

    const content = state.currentUser && state.currentUser.isStaff ? staffContent : studentContent;

    return content.length > 0 && (
        <div>
            <div className="assigned-tickets-header">
                Upcoming Appointments
            </div>
            {content}
        </div>
    )
}
