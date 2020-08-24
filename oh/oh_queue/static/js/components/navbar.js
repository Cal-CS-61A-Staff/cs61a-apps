/* React Components */
let Navbar = ({ state, mode }) => {
    var { currentUser } = state;
    var myTicket = getMyTicket(state);
    if (myTicket && myTicket.group_id) {
        myTicket = null;
    }
    const myGroup = getMyGroup(state);
    var { Link } = ReactRouterDOM;

    const words = mode.split("_");
    const title = words.map(word => word[0].toUpperCase() + word.slice(1)).join(" ");

    const partyAsRoot = isPartyRoot(state);
    const defaultMode = partyAsRoot ? "party" : "queue";

    return (
        <nav className="navbar navbar-default navbar-fixed-top">
            <div className="container">
                <div className="navbar-header">
                    <button type="button" className="navbar-toggle collapsed" data-toggle="collapse"
                            data-target="#navbar-collapse-section">
                        <span className="icon-bar"></span>
                        <span className="icon-bar"></span>
                        <span className="icon-bar"></span>
                    </button>
                    <Link className="navbar-brand" to={"/" + (mode === defaultMode ? "" : mode)}>
                        <strong>{window.courseName} |</strong>{" " + title}
                    </Link>
                </div>
                <div className="collapse navbar-collapse" id="navbar-collapse-section">
                    <ul className="nav navbar-nav navbar-right">

                        {!!myGroup &&
                        <li><Link to={`/groups/${myGroup.id}/`}>My Group</Link></li>}

                        {!!myTicket &&
                        <li><Link to={`/tickets/${myTicket.id}/`}>My Request</Link></li>}

                        {currentUser && state.config.party_enabled &&
                        <li><Link to={partyAsRoot ? "/" : "/party"}>Party</Link></li>}

                        {currentUser &&
                        <li><Link to={partyAsRoot ? "/queue" : "/"}>Queue</Link></li>}

                        {currentUser && JSON.parse(state.config.appointments_open) &&
                        <li><Link to="/appointments">Appointments</Link></li>}

                        {currentUser && currentUser.isStaff &&
                        <li><Link to="/activity_log">Activity Log</Link></li>}

                        {currentUser && currentUser.isStaff &&
                        <li><Link to="/admin">Admin</Link></li>}

                        {currentUser ?
                            <li className="dropdown">
                                <a href="#" className="dropdown-toggle" data-toggle="dropdown"
                                   role="button">{currentUser.name} <span className="caret"/></a>
                                <ul className="dropdown-menu">
                                    {state.config.online_active && currentUser.isStaff && (
                                        <li><Link to="/online_setup">Online Setup</Link></li>
                                    )}
                                    <li><Link to={`/user/${currentUser.id}`}>Ticket History</Link></li>
                                    <li><a href="/logout">Log out</a></li>
                                </ul>
                            </li>
                            :
                            <li><a href="/login/">Staff Login</a></li>
                        }
                    </ul>
                </div>
            </div>
        </nav>
    );
}
