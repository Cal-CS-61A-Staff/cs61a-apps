function TicketLayout({ loadTicket, state, socket, match }) {
    let id = +match.params.id;
    let ticket = getTicket(state, id);

    React.useEffect(() => {
        if (ticket == null) {
            loadTicket(id);
        }
    }, []);

    const [description, setDescription] = React.useState("");

    React.useEffect(() => {if (ticket) setDescription(ticket.description)}, [ticket && ticket.description]);

    const handleDescriptionSubmit = () => {
        app.makeRequest('update_ticket', {
            id,
            description,
        });
    };

    if (ticket == null) {
        if (isLoading(state, id)) {
            return null;  // TODO loading indicator instead of blank screen
        } else {
            return <NotFound/>;
        }
    }

    if (!isStaff(state) && !ticketIsMine(state, ticket, true)) {
        return <NotFound/>;
    }

    let assignment = ticketAssignment(state, ticket);
    let location = ticketLocation(state, ticket);
    let question = ticketQuestion(state, ticket);

    const group = getGroup(state, ticket.group_id);

    return (
        <div>
            <Navbar state={state} mode="queue"/>
            <div className="container">
                <Messages messages={state.messages}/>
                <div className="row ticket">
                    <div className="col-xs-12">
                        <h2 className="ticket-view-name text-center">
                            {group ?
                                `${group.attendees[0].user.shortName}'s Group` :
                                (ticket.status === 'pending' && isStaff(state)) ?
                                    'Help to View Name' :
                                    ticket.user.name
                            }
                            <small
                                className="clearfix">
                                {assignment.name} {question} &middot; {location.name}
                                {location.link && ticket.call_url && ` (${ticket.call_url})`}
                            </small>
                        </h2>
                        <p className="ticket-view-text text-center"> {ticketStatus(state, ticket)} </p>
                    </div>
                </div>
                <div className="row">
                    <div className="col-xs-12 col-md-6 col-md-offset-3">
                        <hr/>
                        <DescriptionBox
                            locked={!!ticket.group_id}
                            state={state}
                            ticket={ticket}
                            prompt="Please describe your issue below:"
                            placeholder="It would be helpful if you could describe your issue. For example, &quot;I have a SyntaxError in my ___ function. I've tried using ____ and ____.&quot;"
                            description={description}
                            onChange={setDescription}
                            onSubmit={handleDescriptionSubmit}
                        />
                    </div>
                </div>
                {!ticket.group_id && <div className="row">
                    <div className="col-xs-12 col-md-6 col-md-offset-3">
                        <hr/>
                        <UpdateLocationBox state={state} ticket={ticket}/>
                    </div>
                </div>}
                <TicketButtons state={state} ticket={ticket}/>
                <div className="row">
                    <div className="col-xs-12 col-md-6 col-md-offset-3">
                        <hr/>
                        <ChatBox
                            key={id}
                            currentUser={state.currentUser}
                            socket={socket}
                            mode={group ? "group" : "ticket"}
                            id={group ? group.id : id}/>
                    </div>
                </div>
                {state.config.ticket_prompt &&
                <div className="row">
                    <div className="col-xs-12 col-md-6 col-md-offset-3">
                        <hr/>
                        <ReactMarkdown source={state.config.ticket_prompt}/>
                    </div>
                </div>
                }
            </div>
        </div>
    );
}
