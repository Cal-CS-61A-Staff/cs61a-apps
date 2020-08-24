class TicketButtons extends React.Component {
  constructor(props) {
    super(props);
    this.assign = this.assign.bind(this);
    this.returnTo = this.returnTo.bind(this);
    this.delete = this.delete.bind(this);
    this.resolveAndNext = this.resolveAndNext.bind(this);
    this.resolveAndLocalNext = this.resolveAndLocalNext.bind(this);
    this.comeBackLater = this.comeBackLater.bind(this);
    this.releaseToAnyone = this.releaseToAnyone.bind(this);
    this.releaseToMe = this.releaseToMe.bind(this);
    this.rerequest = this.rerequest.bind(this);
    this.cancelRerequest = this.cancelRerequest.bind(this);
    this.resolve = this.resolve.bind(this);
    this.unassign = this.unassign.bind(this);
    this.reassign = this.reassign.bind(this);
    this.next = this.next.bind(this);

    this.refresher = null;
  }

  componentDidMount() {
      this.refresher = setInterval(this.forceUpdate.bind(this), 1000);
  }

  componentWillUnmount() {
      clearInterval(this.refresher);
  }

  assign() {
    app.makeRequest('assign', [this.props.ticket.id]);
  }

  returnTo() {
      app.makeRequest("return_to", [this.props.ticket.id]);
  }

  delete() {
    if (!confirm("Delete this ticket?")) return;
    app.makeRequest('delete', [this.props.ticket.id]);
  }

  resolveAndNext() {
    app.makeRequest('resolve', {'ticket_ids': [this.props.ticket.id]}, true)
  }

  resolveAndLocalNext() {
    app.makeRequest('resolve', {'ticket_ids': [this.props.ticket.id], 'local': true}, true)
  }

  comeBackLater() {
      app.makeRequest('juggle', {'ticket_ids': [this.props.ticket.id] }, true)
  }

  releaseToAnyone() {
      if (!confirm("Release this ticket to anyone else?")) return;
      app.makeRequest('release_holds', {'ticket_ids': [this.props.ticket.id] })
  }

  releaseToMe() {
      if (this.props.ticket.helper && !confirm("Take over responsibility for this ticket?")) return;
      app.makeRequest('release_holds', {'ticket_ids': [this.props.ticket.id], to_me: true })
  }

  rerequest() {
      app.makeRequest("rerequest", {'ticket_ids': [this.props.ticket.id] });
  }

  cancelRerequest() {
      app.makeRequest("cancel_rerequest", {'ticket_ids': [this.props.ticket.id] });
  }

  resolve() {
    app.makeRequest('resolve', {'ticket_ids': [this.props.ticket.id]});
  }

  unassign() {
    app.makeRequest('unassign', [this.props.ticket.id]);
  }

  reassign() {
    if (!confirm("Reassign this ticket?")) return;
    app.makeRequest('assign', [this.props.ticket.id]);
  }

  next() {
    app.makeRequest('next', [this.props.ticket.id], true);
  }

  render() {
    let {embedded, state, ticket} = this.props;
    let staff = isStaff(state);

    function makeButton(text, style, action) {
      return (
        <button key={text} onClick={action}
          className={`btn btn-${style} btn-lg btn-block`}>
          {text}
        </button>
      );
    }

    function makeLink(text, style, href) {
      return (
        <a key={text} href={href} target="_blank"
          className={`btn btn-${style} btn-lg btn-block`}>
          {text}
        </a>
      );
    }

    let onlineButtons = [];
    let topButtons = [];
    let bottomButtons = [];

    if (ticket.status === 'pending') {
      bottomButtons.push(makeButton('Delete', 'danger', this.delete));
      if (staff) {
        topButtons.push(makeButton('Help', 'primary', this.assign));
      }
    }
    if (ticket.status === 'assigned') {
      if (!embedded && (ticket.call_url || ticket.helper.call_url)) {
          onlineButtons.push(makeButton('Join Call', 'success',
              () => window.open(ticket.call_url || ticket.helper.call_url, "_blank"))
          );
      }
      if (!embedded && (ticket.doc_url || ticket.helper.doc_url)) {
          onlineButtons.push(makeButton('Open Shared Document', 'info',
              () => window.open(ticket.doc_url || ticket.helper.doc_url, "_blank"))
          );
      }

      bottomButtons.push(makeButton('Resolve', 'default', this.resolve));
      if (staff) {
        if (isTicketHelper(state, ticket)) {
          topButtons.push(makeButton('Resolve and Next in Room', 'primary', this.resolveAndLocalNext));
          topButtons.push(makeButton('Resolve and Next', 'primary', this.resolveAndNext));
          topButtons.push(makeButton('Come Back Later', 'warning', this.comeBackLater));
          bottomButtons.push(makeButton('Requeue', 'default', this.unassign));
        } else {
          topButtons.push(makeButton('Reassign', 'warning', this.reassign));
          topButtons.push(makeButton('Next Ticket', 'default', this.next));
        }
      }
    }
    if (staff && (ticket.status === 'resolved' || ticket.status === 'deleted')) {
      topButtons.push(makeButton('Next Ticket', 'default', this.next));
    }
    if (staff && ticket.status === "assigned" && state.config.show_okpy_backups) {
      topButtons.push(makeLink('View Backups', 'default', 'https://okpy.org/admin/course/' + state.config.okpy_endpoint_id + '/' + encodeURIComponent(ticket.user.email)))
    }
    if (ticket.status === "juggled") {
        const isWaiting = moment.utc(ticket.rerequest_threshold).isAfter();
        if (staff) {
            if (isTicketHelper(state, ticket)) {
                if (isWaiting) {
                    topButtons.push(makeButton("Continue helping (ahead of schedule)", "danger", this.returnTo));
                } else {
                    topButtons.push(makeButton("Continue helping", "warning", this.returnTo));
                }
            } else {
                topButtons.push(makeButton("Take over", "warning", this.releaseToMe));
            }
            if (ticket.helper) {
                topButtons.push(makeButton("Release hold", "danger", this.releaseToAnyone));
            }
            bottomButtons.push(makeButton('Resolve', 'default', this.resolve));
        } else {
            if (isWaiting) {
                const remainingTime = ticketTimeToReRequest(ticket);
                topButtons.push(makeButton("You can re-request help " + remainingTime,
                    "warning disabled"));
            } else {
                topButtons.push(makeButton("Re-request help", "warning", this.rerequest));
            }
            bottomButtons.push(makeButton('Resolve', 'default', this.resolve));
        }
    }
    if (ticket.status === "rerequested") {
        if (staff) {
            if (isTicketHelper(state, ticket)) {
                topButtons.push(makeButton('Continue helping', 'warning', this.returnTo));
            } else {
                topButtons.push(makeButton("Take over", "warning", this.releaseToMe));
            }
            if (ticket.helper) {
                topButtons.push(makeButton("Release hold", "danger", this.releaseToAnyone));
            }
            bottomButtons.push(makeButton('Resolve', 'default', this.resolve));
        } else {
            topButtons.push(makeButton("Help re-requested, wait for staff", "warning disabled"));
            bottomButtons.push(makeButton('Cancel request', 'danger', this.cancelRerequest));
        }
    }

    let onlineHR = onlineButtons.length ? <hr /> : null;
    let hr = topButtons.length && bottomButtons.length ? <hr/> : null;

    if (!(topButtons.length || bottomButtons.length)) {
      return null;
    }

    const contents = (
        <React.Fragment>
            {onlineButtons}
            {onlineHR}
            {topButtons}
            {hr}
            {bottomButtons}
        </React.Fragment>
    );

    if (embedded) {
        return contents;
    }

    return (
      <div className="row">
        <div className="col-xs-12 col-md-6 col-md-offset-3">
          <div className="well">
            {contents}
          </div>
        </div>
      </div>
    );
  }
}
