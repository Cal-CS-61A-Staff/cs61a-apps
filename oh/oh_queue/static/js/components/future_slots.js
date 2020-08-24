function FutureSlots({ state }) {
    const { assignments, appointments, locations, currentUser, messages } = state;
    const filteredAssignments = Object.values(assignments).filter(assignment => assignment.visible).sort((a, b) => a.name.localeCompare(b.name));

    const hiddenTypes = (currentUser && currentUser.isStaff) ? ["resolved"] : ["resolved", "hidden"];

    const currentAppointments = appointments.filter(({ status }) => !hiddenTypes.includes(status));

    const [compact, setCompact] = React.useState(false);
    const [hideFull, setHideFull] = React.useState(false);

    React.useEffect(() => setCompact(currentUser && !currentUser.isStaff), [currentUser && currentUser.isStaff]);

    const days = new Map();
    for (const appointment of currentAppointments) {
        if (appointment.status === "active") {
            continue;
        }
        if (hideFull && appointment.signups.length >= appointment.capacity) {
            continue;
        }
        const date = formatAppointmentDate(appointment);
        if (!days.has(date)) {
            days.set(date, []);
        }
        days.get(date).push(appointment)
    }

    for (const value of days.values()) {
        value.sort(appointmentTimeComparator);
    }

    const [openedAppointment, setOpenedAppointment] = React.useState();
    const [openedSignup, setOpenedSignup] = React.useState();

    const [modalOpen, setModalOpen] = React.useState(false);

    const handleAddClick = (appointmentID, signup) => {
        setOpenedAppointment(appointmentID);
        setOpenedSignup(signup);
        setModalOpen(true);
    };

    const handleSubmit = () => {
        setModalOpen(false);
    };

    const mySignups = [];
    for (const appointment of currentAppointments) {
        for (const signup of appointment.signups) {
            if (signup.user && signup.user.id === currentUser.id) {
                mySignups.push({ appointment, signup });
            }
        }
    }

    return (
        <React.Fragment>
            {currentUser && !currentUser.isStaff && (
                <ConfirmedAppointment
                    mySignups={mySignups}
                    locations={locations}
                    assignments={assignments}
                />
            )}
            {currentUser && currentUser.isStaff && (
                <StaffUpcomingAppointments
                    myAppointments={getMyAppointmentsStaff(state)}
                    locations={locations}
                />
            )}
            {(!currentUser || currentUser.isStaff) && <br />}
            <div className="container">
                <Messages messages={messages}/>
                {/*<FilterControls state={state} />*/}
                <div className="alert alert-warning alert-dismissable fade in" role="alert">
                    <button type="button" className="close" aria-label="Close" data-dismiss="alert">
                        <span aria-hidden="true">&times;</span>
                    </button>
                    <h4>Appointment Limits</h4>
                    <h5>
                        You cannot enroll in more than
                        {" "}
                        {state.config.daily_appointment_limit}
                        {" "}
                        appointments per day, or more than
                        {" "}
                        {state.config.weekly_appointment_limit}
                        {" "}
                        per week. You also cannot be signed up for more than
                        {" "}
                        {state.config.simul_appointment_limit}
                        {" "}
                        appointments that have not yet occurred.
                    </h5>
                  </div>
                {(!currentUser || currentUser.isStaff) && <AppointmentButtons />}
                <FancyToggle checked={compact} onChange={setCompact} offText="Regular" onText="Compact" />
                {" "}
                <FancyToggle checked={hideFull} onChange={setHideFull} offText="Show All" onText="Hide Full" />
                {Array.from(days.entries()).map(([day, dayAppointments]) =>
                    <div>
                        <h3> {day} </h3>
                        <div className={"card-holder " + (compact ? "compact-card-holder" : "")}>
                            {dayAppointments.map(appointment => {
                                    return (
                                        <AppointmentCard
                                            locations={locations}
                                            appointment={appointment}
                                            currentUser={currentUser}
                                            assignments={assignments}
                                            onStudentSignup={handleAddClick}
                                            compact={compact}
                                        />
                                    )
                                }
                            )}
                        </div>
                        <hr/>
                    </div>)
                }
            </div>
            <AppointmentOverlay
                assignments={filteredAssignments}
                appointment={openedAppointment}
                signup={openedSignup}
                staffMode={currentUser && currentUser.isStaff}
                isOpen={modalOpen}
                onSubmit={handleSubmit}
            />
        </React.Fragment>
    );
}
