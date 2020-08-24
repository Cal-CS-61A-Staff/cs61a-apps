let PresenceIndicator = ({ state, hideWaitTime, hideWelcome }) => {
    let presence = state.presence;
    let numStudentsOnline = presence && presence.students ? presence.students : 0;
    let numStaffOnline = presence && presence.staff ? presence.staff : 0;
    let color = numStaffOnline ? 'success' : 'warning';
    let pendingTickets = getTickets(state, 'pending');
    let assignedTickets = getTickets(state, 'assigned');

    var studentMessage = numStudentsOnline + " students";
    var staffMessage = numStaffOnline + " assistants";

    if (numStudentsOnline === 1) {
        studentMessage = studentMessage.slice(0, -1)
    }
    if (numStaffOnline === 1) {
        staffMessage = staffMessage.slice(0, -1)
    }

    let message = studentMessage + " and " + staffMessage + " currently online."

    // PARAM 1: expected service time ~ Exponential(1/10)
    var avgHelpTime = 10

    // how many assistants are unoccupied
    var availableAssistants = numStaffOnline - assignedTickets.length

    // how many students need help, assuming all avaiable assistants are assigned
    var stillNeedHelp = Math.max(0, pendingTickets.length - availableAssistants)

    var waitColor = "#646468"

    // catch if there actually are no assistants available
    if (numStaffOnline == 0) {
        var timeRange = "??"
    } else {
        // min of numStaffOnline exponentials is exponential, take expectation
        var expectedWaitFirst = Math.ceil(avgHelpTime / numStaffOnline)
        // standard deviation of exponential equals the expectation
        var stdDev = expectedWaitFirst

        // expectation for stillNeedHelp + 1th student on queue
        var expectedWaitTotal = (stillNeedHelp + 1) * expectedWaitFirst

        // PARAM 2: (75% conf interval by CLT, 1.15 is from zscore of Normal)
        var bound = 1.15 * stdDev / Math.sqrt(numStaffOnline)

        // interval bounds
        var estWaitTimeMin = Math.max(0, Math.floor(expectedWaitTotal - bound))
        var estWaitTimeMax = Math.ceil(expectedWaitTotal + bound)

        // colors for the time
        if (expectedWaitTotal <= 5) {
            waitColor = "#009900"
        } else if (expectedWaitTotal < 10) {
            waitColor = "#739900"
        } else if (expectedWaitTotal < 25) {
            waitColor = "#cc5200"
        } else {
            waitColor = "#ff0000"
        }

        // concatenate time range string
        var timeRange = estWaitTimeMin + " - " + estWaitTimeMax
        if (estWaitTimeMax > 120) {
            timeRange = "> 120"
        }
    }

    var welcomeMessage = state.config.welcome;

    const openQueue = () => {
        app.makeRequest(`update_config`, {
            key: "is_queue_open",
            value: "true",
        });
    };

    return (
        <div className="col-xs-12">

            {!hideWaitTime && state.config.is_queue_open === "false" && (state.config.party_enabled || isStaff(state)) &&
            <div className="alert alert-danger alert-dismissable fade in" role="alert">
                <button type="button" className="close" aria-label="Close" data-dismiss="alert">
                    <span aria-hidden="true">&times;</span>
                </button>
                <h3>The queue is currently closed!</h3>
                {state.currentUser && state.currentUser.isStaff && (
                    <button className="btn btn-primary" onClick={openQueue}>Open queue</button>
                )}
            </div>
            }

            {!hideWelcome && <div className="alert alert-info alert-dismissable fade in" role="alert">
                <button type="button" className="close" aria-label="Close" data-dismiss="alert">
                    <span aria-hidden="true">&times;</span>
                </button>
                <ReactMarkdown source={welcomeMessage}/>
            </div>}

            {state.config.online_active === "true" && state.currentUser && state.currentUser.isStaff &&
            [state.config.students_set_online_link, state.config.students_set_online_doc].includes("false") && (
                <div className="alert alert-warning alert-dismissable fade in" role="alert">
                    <button type="button" className="close" aria-label="Close" data-dismiss="alert">
                        <span aria-hidden="true">&times;</span>
                    </button>
                    <h4>Configure Online Queue Settings</h4>
                    <h5>
                        Remember to go to <Link to="/online_setup">Online Setup</Link> to configure
                        your settings for
                        video calls and shared documents, otherwise you will not be able to interact
                        with
                        students on the Online Queue.
                    </h5>
                </div>
            )}

            {!hideWaitTime &&
            <div className={`alert alert-${color} alert-dismissable fade in`} role="alert">
                <button type="button" className="close" aria-label="Close" data-dismiss="alert">
                    <span aria-hidden="true">&times;</span>
                </button>
                <h4>Estimated wait time: <font
                    color={waitColor}><strong>{timeRange}</strong></font> minutes</h4>
                <h5>{message}</h5>
                <MagicWordDisplay state={state}/>
                {presence && state.currentUser && state.currentUser.isStaff && (
                    <React.Fragment>
                        <p>
                            <a data-toggle="collapse" href="#collapseExample"
                               role="button" aria-expanded="false" aria-controls="collapseExample">
                                See online assistants.
                            </a>
                        </p>
                        <div className="collapse" id="collapseExample">
                            <div className="card card-body">
                                <ul>
                                    {presence.staff_list.map(
                                        ([email, name]) => <li>{name} (<a
                                            href={`mailto:${email}`}> {email}</a>)</li>,
                                    )}
                                </ul>
                            </div>
                        </div>
                    </React.Fragment>
                )}
            </div>}
        </div>
    );
}
