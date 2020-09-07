function AdminPartyManager({ state }) {
    return (
        <React.Fragment>
            <AdminOptionsManager>
                <tr>
                    <td>Should students be able to create and join HW Party groups?</td>
                    <td className="col-md-1">
                        <ConfigLinkedToggle
                            config={state.config}
                            configKey="party_enabled"
                        />
                    </td>
                </tr>
                <tr>
                    <td>Should students be able to create individual tickets during HW Party?</td>
                    <td className="col-md-1">
                        <ConfigLinkedToggle
                            config={state.config}
                            configKey="allow_private_party_tickets"
                        />
                    </td>
                </tr>
            </AdminOptionsManager>
        </React.Fragment>
    );
}
