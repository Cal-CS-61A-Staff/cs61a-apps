function AdminAppointmentsManager({ state }) {
    const [sheetUrl, setSheetUrl] = React.useState("");
    const [sheetName, setSheetName] = React.useState("");

    const [isLoading, setIsLoading] = React.useState(false);

    const handleSheetUrlChange = (e) => {
        setSheetUrl(e.target.value);
    };
    const handleSheetNameChange = (e) => {
        setSheetName(e.target.value);
    };

    const submit = () => {
        setIsLoading(true);
        app.makeRequest("upload_appointments", {
            sheetUrl, sheetName,
        }, false, () => {setIsLoading(false)});
    };

    return (
        <React.Fragment>
            <AdminOptionsManager>
                <tr>
                    <td>Should students be able to make appointments?</td>
                    <td className="col-md-1">
                        <ConfigLinkedToggle
                            config={state.config}
                            configKey="appointments_open"
                            offText="No"
                            onText="Yes"
                        />
                    </td>
                </tr>
                <tr>
                    <td>
                        <p>
                            How many appointments should a student be able to make daily?
                        </p>
                    </td>
                    <td className="col-md-3">
                        <ConfigLinkedNumeric
                            config={state.config}
                            configKey="daily_appointment_limit"
                        />
                    </td>
                </tr>
                <tr>
                    <td>
                        <p>
                            How many appointments should a student be able to make weekly?
                        </p>
                    </td>
                    <td className="col-md-3">
                        <ConfigLinkedNumeric
                            config={state.config}
                            configKey="weekly_appointment_limit"
                        />
                    </td>
                </tr>
                <tr>
                    <td>
                        <p>
                            How many appointments should a student have be pending simultaneously?
                        </p>
                    </td>
                    <td className="col-md-3">
                        <ConfigLinkedNumeric
                            config={state.config}
                            configKey="simul_appointment_limit"
                        />
                    </td>
                </tr>
            </AdminOptionsManager>
            <form>
                <div className="input-group appointment-input">
                    <input id="url-selector" type="text" className="form-control" placeholder="Link to a spreadsheet containing appointments" required value={sheetUrl} onChange={handleSheetUrlChange} />
                    <input id="sheet-selector" className="form-control form-right" type="text" name="question" title="Sheet name" placeholder="Sheet name" required value={sheetName} onChange={handleSheetNameChange}/>
                      <span className="input-group-btn">
                        <button className={"btn btn-default " + (isLoading ? "is-loading" : "")} type="button" onClick={submit}>
                            Update
                        </button>
                      </span>
                </div>
                <small>
                    You must share this spreadsheet with the 61A service account <a href="mailto:secure-links@ok-server.iam.gserviceaccount.com">secure-links@ok-server.iam.gserviceaccount.com</a>.
                </small>
            </form>
        </React.Fragment>
    );
}
