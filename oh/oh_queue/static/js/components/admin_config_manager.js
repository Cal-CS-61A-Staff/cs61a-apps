function AdminConfigManager({ state: { config } }) {
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
                        <td>Should the queue be open to new tickets?</td>
                        <td className="col-md-3">
                            <ConfigLinkedToggle
                                config={config}
                                configKey="is_queue_open"
                                offText="Closed"
                                onText="Open"
                            />
                        </td>
                    </tr>
                    <tr>
                        <td>Should the description field be required for new tickets?</td>
                        <td className="col-md-1">
                            <ConfigLinkedToggle
                                config={config}
                                configKey="description_required"
                                offText="No"
                                onText="Yes"
                            />
                        </td>
                    </tr>
                    <tr>
                        <td>Should staff members see a link to recent OKPy backups?</td>
                        <td className="col-md-1">
                            <ConfigLinkedToggle
                                config={config}
                                configKey="show_okpy_backups"
                                offText="No"
                                onText="Yes"
                            />
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <p>What type of magic word should the queue require to submit new
                                tickets?</p>
                            <ul>
                                <li>Text = staff will provide a hard-coded magic word</li>
                                <li>Time-based Numeric = the magic word will be a 4-digit number
                                    that changes every minute. This number is displayed under
                                    "Estimated Wait Time" on the homepage (staff view only).
                                </li>
                            </ul>
                        </td>
                        <td className="col-md-3">
                            <AdminMagicWordForm config={config} />
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <p>What should the delay be before students can request to be taken
                                off hold? (in minutes)</p>
                        </td>
                        <td className="col-md-3">
                            <ConfigLinkedNumeric
                                config={config}
                                configKey="juggling_delay"
                            />
                        </td>
                    </tr>
                    </tbody>
                </table>
            </div>
            <ConfigLinkedMarkdownInput
                title="Welcome Message"
                placeholder="Welcome to the OH Queue!"
                config={config}
                configKey="welcome"
            />
            <ConfigLinkedMarkdownInput
                title="Ticket Prompt"
                placeholder="Have fun with your ticket!"
                config={config}
                configKey="ticket_prompt"
            />
        </React.Fragment>
    );
}
