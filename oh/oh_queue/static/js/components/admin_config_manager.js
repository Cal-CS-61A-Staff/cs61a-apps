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
              <td>Should only students on the roster be allowed to log in?</td>
              <td className="col-md-1">
                <ConfigLinkedToggle
                  config={config}
                  configKey="only_registered_students"
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
                <p>
                  What should the delay be before students can request to be
                  taken off hold? (in minutes)
                </p>
              </td>
              <td className="col-md-3">
                <ConfigLinkedNumeric
                  config={config}
                  configKey="juggling_delay"
                />
              </td>
            </tr>
            <tr>
              <td>
                <p>
                  When an email is sent from the course, what should the email be? (berkeley.edu email)
                </p>
              </td>
              <td className="col-md-3">
                <ConfigLinkedText
                  config={config}
                  configKey="course_email"
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
