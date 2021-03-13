function AdminTicketsManager({ state: { config } }) {
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
              <td>
                <p>
                  What type of magic word should the queue require to submit new
                  tickets?
                </p>
                <ul>
                  <li>Text = staff will provide a hard-coded magic word</li>
                  <li>
                    Time-based Numeric = the magic word will be a 4-digit number
                    that changes every minute. This number is displayed under
                    "Estimated Wait Time" on the homepage (staff view only).
                  </li>
                </ul>
              </td>
              <td className="col-md-3">
                <AdminMagicWordForm config={config} />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <ConfigLinkedText
        title="Description Template"
        placeholder={"Points of confusion:\n\n Things I've tried:"}
        config={config}
        configKey="default_description"
        lines={10}
        optional
      />
    </React.Fragment>
  );
}
