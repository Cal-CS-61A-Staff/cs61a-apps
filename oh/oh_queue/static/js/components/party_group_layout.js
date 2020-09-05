const { Link } = ReactRouterDOM;

function PartyGroupLayout({ state, match, loadGroup, socket }) {
    const groupID = +match.params.id;

    if (!getGroup(state, groupID)) {
        loadGroup(groupID);
        return "loading...";
    }
    const group = getGroup(state, groupID);
    const ticket = getTicket(state, group.ticket_id);
    const location = state.locations[group.location_id];
    const ticketActive = ticket && !["resolved", "deleted"].includes(ticket.status);

    const inGroup = groupIsMine(state, group);

    const handleLeaveGroup = () => {
        const leave = () => app.makeRequest("leave_group", group.id, true);

        if (ticketActive && ticket.user.id === state.currentUser.id) {
            Swal.fire({
              title: 'Are you sure?',
              text: "You have created a ticket for this group. If you leave the group, the" +
                  " ticket will be deleted!",
              icon: 'warning',
              showCancelButton: true,
              confirmButtonColor: '#3085d6',
              cancelButtonColor: '#d33',
              confirmButtonText: 'Yes, do it!'
            }).then((result) => {
              if (result.value) {
                leave();
              }
            });
        } else {
            leave();
        }
    };

    const actionButton = inGroup ? (
        <React.Fragment>
            <PartyGroupLayoutButton
                color="default"
                disabled={ticketActive || !JSON.parse(state.config.is_queue_open)}
                onClick={() => app.makeRequest("create_group_ticket", {id: group.id})}
            >
                {ticketActive ?
                    `${ticket.user.shortName} has asked for help` :
                    JSON.parse(state.config.is_queue_open) ?
                        "Ask for Help (as a group)" :
                        "Queue is currently closed"
                }
            </PartyGroupLayoutButton>
            <hr />
            <PartyGroupLayoutButton color="danger" onClick={handleLeaveGroup}>
                Leave Group
            </PartyGroupLayoutButton>
        </React.Fragment>
    ) : (
        <React.Fragment>
            {group.group_status === "active" &&
                <React.Fragment>
                    <PartyGroupLayoutButton color="primary" onClick={() => app.makeRequest("join_group", group.id, true)}>
                        Join Group
                    </PartyGroupLayoutButton>
                    <hr />
                </React.Fragment>
            }
            <Link to="/">
                <PartyGroupLayoutButton color="default" onClick={() => null}>
                    Return to Home
                </PartyGroupLayoutButton>
            </Link>
        </React.Fragment>
    );

    let onlineButtons = null;
    if (location.online && group.group_status === "active" && inGroup) {
        const callButton = (location.link || group.call_url) && (
            <PartyGroupLayoutButton color="success" onClick={() => window.open(location.link || group.call_url, "_blank")}>
                Join Call
            </PartyGroupLayoutButton>
        );
        const docButton = group.doc_url && (
            <PartyGroupLayoutButton color="info" onClick={() => window.open(group.doc_url, "_blank")}>
                Open Shared Document
            </PartyGroupLayoutButton>
        );
        if (callButton || docButton) {
            onlineButtons = (
                <React.Fragment>
                    {callButton}
                    {docButton}
                </React.Fragment>
            )
        }
    }

    const [description, setDescription] = React.useState("");

    React.useEffect(() => {if (group) setDescription(group.description)}, [group && group.description]);

    const handleDescriptionSubmit = () => {
        app.makeRequest('update_group', {
            id: groupID,
            description,
        });
    };

    return (
        <div>
            <Navbar state={state} mode="party"/>
            <div className="container">
                <Messages messages={state.messages}/>
                <br/>
                <h2 className="list-group-item-heading text-center">
                    {state.assignments[group.assignment_id].name}
                    {" "}
                    {ticketQuestion(state, group)}
                    <small className="clearfix">
                        {group.group_status[0].toUpperCase() + group.group_status.slice(1)}
                        {" "}
                        &middot;
                        {" "}
                        {location.name}
                        {location.link && group.call_url && ` (${group.call_url})`}
                    </small>
                    <p className="ticket-view-text text-center">Created {ticketTimeAgo(group)}.</p>
                    </h2>
                    <div className="row">
                        <div className="col-xs-12 col-md-6 col-md-offset-3">
                            <hr/>
                            <DescriptionBox
                                editable
                                locked={!inGroup}
                                state={state}
                                ticket={group}
                                description={description}
                                prompt="Encourage others to join the group!"
                                placeholder="Hi! Anyone else want to work on this problem with me?"
                                onChange={setDescription}
                                onSubmit={handleDescriptionSubmit}
                            />
                        </div>
                    </div>
                    <div className="row">
                        <div className="col-xs-12 col-md-6 col-md-offset-3">
                            <UpdateAssignmentBox state={state} group={group} />
                        </div>
                    </div>
                    <hr />
                    {(onlineButtons || actionButton) && (
                        <div className="row">
                            <div className="col-xs-12 col-md-6 col-md-offset-3">
                                <div className="well">
                                    {onlineButtons}
                                    {actionButton}
                                </div>
                            </div>
                        </div>
                    )}
                <div className="card-holder">
                    {ticketActive && (
                        <div>
                            <div className="panel panel-primary">
                                <div className="panel-heading">
                                    <h3 className="panel-title">
                                        Your Ticket
                                    </h3>
                                </div>
                                <div className="panel-body">
                                    <p className="ticket-view-text text-center"> {ticketStatus(state, ticket)} </p>
                                    <hr />
                                    <TicketButtons embedded state={state} ticket={ticket} />
                                </div>
                            </div>
                        </div>
                    )}
                    <div>
                        {group.attendees.map(attendance => (
                            <div className="panel panel-default">
                                <div className="panel-heading">
                                    <h3 className="panel-title">
                                        {attendance.user.isStaff ? "Staff" : "Student"}
                                    </h3>
                                </div>
                                <div className="panel-body">
                                    {attendance.user.name}
                                </div>
                            </div>
                        ))}
                    </div>
                    <ChatBox
                        key={group.id}
                        currentUser={state.currentUser}
                        socket={socket}
                        id={group.id}
                        mode="group"
                    />
                </div>

                {state.config.ticket_prompt &&
                <div className="row">
                    <div className="col-xs-12 col-md-6 col-md-offset-3 text-center">
                        <hr/>
                        <ReactMarkdown source={state.config.ticket_prompt}/>
                    </div>
                </div>
                }
            </div>
        </div>
    )
}

function PartyGroupLayoutButton({ color, children, disabled, onClick }) {
    return (
        <button className={`btn btn-${color} btn-lg btn-block`}
                disabled={disabled}
                onClick={onClick}>
            {children}
        </button>
    );
}
