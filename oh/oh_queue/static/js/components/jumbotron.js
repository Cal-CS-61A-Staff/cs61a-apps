let Jumbotron = ({ state }) => {
    var isQueueOpen = state.config && JSON.parse(state.config.is_queue_open);
    const appointments = JSON.parse(state.config.appointments_open);
    const party_enabled = state.config.party_enabled;
    if (!state.currentUser) {
        var titleText = 'Hi! Please sign in';
        var subtitleText = 'Sign in with your course OK account to request help';
        var contents = (
            <a className="btn btn-block btn-jumbo btn-outline" href="/login">
                Sign in with Ok
            </a>
        );
    } else if (!isQueueOpen) {
        var titleText = `Hello, ${state.currentUser.shortName}`;
        var subtitleText = 'The queue is currently closed. Check back later!';
        var contents = <RequestForm state={state} />;
    } else {
        var titleText = `Hello, ${state.currentUser.shortName}`;
        var subtitleText = 'Fill out the form to request help!';
        var contents = <RequestForm state={state} />;
    }

    if (state.currentUser && party_enabled) {
        subtitleText = "Join an existing group, or create a new one!";
    }
    else if (state.currentUser && appointments && !isQueueOpen) {
        subtitleText = " Click the button to make an appointment for a future OH!"
    }

    return (
        <div className="jumbotron blue">
            <div className="container">
                <section className="page-header">
                    <div className="row">
                        <Messages messages={state.messages}/>
                    </div>
                    <div className="row">
                        <div className="col-md-7 col-lg-8">
                            <h3 className="truncate">{titleText}</h3>
                            <p className="truncate">{subtitleText}</p>
                        </div>
                        <div className="col-md-5 col-lg-4">
                            <div className="request-form">
                                {contents}
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
}
