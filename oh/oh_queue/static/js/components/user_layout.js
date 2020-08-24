function UserLayout({ state, match }) {
    const userID = +match.params.id;


    const [userData, setUserData] = React.useState({});
    const [isLoading, setIsLoading] = React.useState(false);

    if (app && !isLoading && Object.keys(userData).length === 0) {
        setIsLoading(true);
        app.makeRequest("get_user", userID, false, (userData) => {
            setUserData(userData);
        })
    }

    if (Object.keys(userData).length === 0) {
        return null;
    }

    const ticketRows = userData.tickets.map(ticket => (
        [moment.utc(ticket.created), <Row
            title={ticket.user.name + "'s Ticket"}
            link={`/tickets/${ticket.id}`}
            prop1={moment().to(moment.utc(ticket.created))}
            prop2={state.locations[ticket.location_id].name}
        />]
    ));

    const appointmentRows = userData.appointments.map(appointment => {
        const { id, location_id, signups, start_time } = appointment;

        const students = signups.map(({ user: { name } }) => name);

        let studentNameList;
        if (students.length === 0) {
            studentNameList = "nobody"
        } else if (students.length === 1) {
            studentNameList = students[0];
        } else {
            studentNameList = students.slice(0, students.length - 1).join(", ") + " and " + students[students.length - 1];
        }

        const title = "Section with " + studentNameList;

        return (
            [getAppointmentStartTime(appointment), <Row
                    title={title}
                    link={`/appointments/${id}`}
                    prop1={moment().to(getAppointmentStartTime({ start_time }))}
                    prop2={state.locations[location_id].name}
                />
            ]
        )
    });

    const rows = [].concat(ticketRows, appointmentRows).sort((a, b) => -timeComparator(a[0], b[0])).map(x => x[1]);

    return (
        <div>
            <Navbar state={state} mode="activity_log"/>
            <OfflineIndicator offline={state.offline && state.loaded}/>
            <div className="jumbotron">
                <div className="container">
                    <h2> { userData.user.name } </h2>
                    <p>{ userData.user.email }</p>
                    <div className="activity-buttons">
                        <Link to="/activity_log" className="btn btn-warning">Back to list</Link>
                    </div>
                </div>
            </div>
            <div className="container">
                <h3>History</h3>
                <div className="queue">
                    {rows}
                </div>
            </div>
        </div>
    )
}
