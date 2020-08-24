function AdminSlackManager({ state: { config } }) {
    return (
        <React.Fragment>
            <div className="table-responsive">
                <table className="table table-hover">
                    <thead>
                    <tr>
                        <th>Option</th>
                        <th className="col-md-3">Value</th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr>
                        <td>Should the queue send a Slack notification when the queue is long?</td>
                        <td className="col-md-3">
                            <ConfigLinkedToggle
                                config={config}
                                configKey="slack_notif_long_queue"
                            />
                        </td>
                    </tr>
                    <tr>
                        <td>Should the queue send a Slack notification summarizing daily appointments?</td>
                        <td className="col-md-1">
                            <ConfigLinkedToggle
                                config={config}
                                configKey="slack_notif_appt_summary"
                            />
                        </td>
                    </tr>
                    <tr>
                        <td>Should the queue send a Slack notification if an appointment is missed?</td>
                        <td className="col-md-1">
                            <ConfigLinkedToggle
                                config={config}
                                configKey="slack_notif_missed_appt"
                            />
                        </td>
                    </tr>
                    </tbody>
                </table>
                <p>
                    To setup Slack, visit
                    {" "}
                    <a href="https://auth.apps.cs61a.org" target="_blank">Auth</a>
                    {" "}
                    and register a Slack channel with the purpose <code>oh-queue</code>.
                    Then check that it works!
                </p>
                <p>
                    <button className="btn btn-primary" onClick={() => app.makeRequest("test_slack")}>
                        Send a test message
                    </button>
                    <button
                        style={{"margin-left": 5}}
                        className="btn btn-warning"
                        onClick={() => app.makeRequest("appointment_summary")}
                    >
                        Send daily appointment summary
                    </button>
                </p>
            </div>
        </React.Fragment>
    );
}
