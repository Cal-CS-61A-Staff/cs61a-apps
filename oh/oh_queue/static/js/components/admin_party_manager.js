function AdminPartyManager({ state }) {
  return (
    <React.Fragment>
      <AdminOptionsManager>
        <tr>
          <td>What should {state.config.party_name} mode be called?</td>
          <td className="col-md-1">
            <ConfigLinkedText config={state.config} configKey="party_name" />
          </td>
        </tr>
        <tr>
          <td>
            Should students be able to create and join {state.config.party_name}{" "}
            groups?
          </td>
          <td className="col-md-1">
            <ConfigLinkedToggle
              config={state.config}
              configKey="party_enabled"
            />
          </td>
        </tr>
        <tr>
          <td>
            Should students be able to create individual tickets while{" "}
            {state.config.party_name} mode is enabled?
          </td>
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
