function GroupCard({ group, state }: { group: Group, state: State }) {
    const { Link } = ReactRouterDOM;

    let panelColor = "panel-default";

    const inGroup = groupIsMine(state, group);

    if (inGroup) {
        panelColor = "panel-primary";
    } else {
        panelColor = "panel-default";
    }

    const panelClass = classNames({
        'panel': true,
        [panelColor]: true,
    });

    const ownerName = group.attendees[0].user.shortName;

    const joinText = group.attendees.length === 1 ? `Join ${ownerName}!` : `Join ${ownerName} and ${group.attendees.length - 1} others!`;

    const joinGroup = () => {
        const join = () => app.makeRequest("join_group", group.id, true);
        const ticket = getMyTicket(state);
        if (ticket && ticket.group_id) {
            Swal.fire({
                title: 'Are you sure?',
                text: "You have created a ticket for your previous group. If you switch groups," +
                    " that ticket will be deleted",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Yes, do it!'
            }).then((result) => {
                if (result.value) {
                    join();
                }
            });
        } else {
            join()
        }
    };

    return (
        <div className={panelClass}>
            <div className="panel-heading">
                {state.assignments[group.assignment_id].name}
                {" "}
                {ticketQuestion(state, group)}
                {" "}
                &middot;
                {" "}
                {state.locations[group.location_id].name}
                <div className="btn-group" role="group" style={{float: "right"}}>
                {isStaff(state) && (
                    <button type="button"
                            className="btn btn-xs btn-default"
                            onClick={() => app.makeRequest("delete_group", group.id)}
                    >
                        <span className="glyphicon glyphicon-trash" aria-hidden="true"/>
                    </button>
                )}
            </div>

            </div>
            <div className="panel-body">
                {inGroup ? (
                    <p><b>
                        You are in this group.
                    </b></p>
                ) : (
                    <p>
                        {state.currentUser ? ownerName : "A student"} is looking to collaborate!
                    </p>
                )}
                {group.description ? (
                    <blockquote style={{ fontSize: 15 }}>
                        {group.description}
                    </blockquote>
                ) : (
                    <p><i>No description</i></p>
                )}
                <p>
                    Created {ticketTimeAgo(group)}.
                </p>
                {state.currentUser && <Link to={inGroup ? `groups/${group.id}` : null}>
                    <button className={inGroup ? "btn btn-primary" : "btn btn-default"} type="button"
                            onClick={inGroup ? null : joinGroup}>
                        {inGroup ? "Return to group" : joinText}
                    </button>
                </Link>}
            </div>
        </div>
    )
}
