/* This component holds the global application state, and manages the websocket
 * connection. To update the state, call a method on the global "app" object,
 * e.g. as
 *
 *     app.addMessage("Something bad happened", "danger");
 *
 * Because it sits at the root of React heirarchy, any state changes in the app
 * will cause the entire app to re-render, so any state changes are reflected
 * instantly.
 *
 * All other React components are "stateless". Many of them are simply pure
 * functions that take the state and produce HTML. A few are slightly more
 * complicated in that they have to interact with jQuery or the network.
 *
 * NB: calling app methods inside a render() method will result in an infinite
 * loop.
 */
class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = initialState;
    this.socket = new Socket();

    this.socket.on("connect", () => {
      this.setOffline(false);
    });
    this.socket.on("disconnect", () => this.setOffline(true));
    this.socket.on("state", (data, callback) => {
      this.updateState(data);
      if (callback) {
        callback();
      }
    });
    this.socket.on("event", (data) => this.updateTicket(data));
    this.socket.on("presence", (data) => this.updatePresence(data));
    this.socket.on("appointment_event", (data) => this.updateAppointment(data));
    this.socket.on("group_event", (data) => this.updateGroup(data));

    this.loadTicket = this.loadTicket.bind(this);
    this.loadAppointment = this.loadAppointment.bind(this);
    this.loadGroup = this.loadGroup.bind(this);
  }

  refresh() {
    this.setState(this.state);
  }

  setOffline(offline) {
    this.state.offline = offline;
    this.refresh();
  }

  updateState(data) {
    if (Array.isArray(data.assignments)) {
      this.state.assignments = {};
      for (var assignment of data.assignments) {
        this.state.assignments[assignment.id] = assignment;
      }
    }
    if (Array.isArray(data.locations)) {
      this.state.locations = {};
      for (var location of data.locations) {
        this.state.locations[location.id] = location;
      }
    }
    if (Array.isArray(data.tickets)) {
      for (var ticket of data.tickets) {
        setTicket(this.state, ticket);
      }
    }
    if (data.hasOwnProperty("config")) {
      this.state.config = data.config;
      for (const key of [
        "daily_appointment_limit",
        "weekly_appointment_limit",
        "simul_appointment_limit",
        "show_okpy_backups",
        "slack_notif_long_queue",
        "slack_notif_appt_summary",
        "slack_notif_missed_appt",
        "party_enabled",
        "allow_private_party_tickets",
      ]) {
        this.state.config[key] = JSON.parse(this.state.config[key]);
      }
    }
    if (data.hasOwnProperty("current_user")) {
      this.state.currentUser = data.current_user;
    }
    if (data.hasOwnProperty("appointments")) {
      this.state.appointments = Array.from(data.appointments).sort(
        appointmentTimeComparator
      );
    }
    if (data.hasOwnProperty("groups")) {
      this.state.groups = Array.from(data.groups).sort((x) => x.id);
    }
    this.state.loaded = true;
    this.refresh();
  }

  updatePresence(data) {
    this.state.presence = data;
    this.refresh();
  }

  shouldNotify(ticket, type) {
    return isStaff(this.state) && type === "create";
  }

  updateAppointment({ appointment, type }) {
    setAppointment(this.state, appointment, () => {
      this.router.history.push("/appointments/" + appointment.id);
    });
    this.refresh();
  }

  updateTicket(data) {
    setTicket(this.state, data.ticket);
    this.refresh();

    var ticket = data.ticket;
    switch (data.type) {
      case "assign":
      case "delete":
      case "resolve":
        if (isStaff(this.state)) {
          cancelNotification(ticket.id + ".create");
        }
        break;
      case "create":
      case "describe":
      case "unassign":
      case "update_location":
        if (isStaff(this.state) && ticket.status === "pending") {
          var assignment = ticketAssignment(this.state, ticket);
          var location = ticketLocation(this.state, ticket);
          var question = ticketQuestion(this.state, ticket);
          notifyUser(
            "New request for " + assignment.name + " " + question,
            location.name,
            ticket.id + ".create"
          );
        }
        break;
    }
  }

  updateGroup(data) {
    setGroup(this.state, data.group);
    this.refresh();
  }

  loadTicket(id) {
    loadTicket(this.state, id);
    this.refresh();
    this.socket.emit("load_ticket", id, (ticket) => {
      receiveTicket(this.state, id, ticket);
      this.refresh();
    });
  }

  loadAppointment(id) {
    if (isStaff(this.state)) {
      this.socket.emit("load_appointment", id, (appointment) => {
        setAppointment(this.state, appointment);
        this.refresh();
      });
    }
  }

  loadGroup(id) {
    if (isStaff(this.state)) {
      this.socket.emit("load_group", id, (group) => {
        setGroup(this.state, group);
        this.refresh();
      });
    }
  }

  toggleFilter() {
    this.state.filter.enabled = !this.state.filter.enabled;
    this.refresh();
  }

  setFilter(filter) {
    filter.enabled = !!this.state.filter.enabled;
    this.state.filter = filter;
    this.refresh();
  }

  addMessage(message, category) {
    addMessage(this.state, message, category);
    this.refresh();
  }

  clearMessage(id) {
    clearMessage(this.state, id);
    this.refresh();
  }

  makeRequest(eventType, request, follow_redirect = false, callback) {
    if (typeof request === "function") {
      follow_redirect = request;
      request = undefined;
    }
    if (typeof follow_redirect === "function") {
      callback = follow_redirect;
      follow_redirect = false;
    }
    let cb = (response) => {
      if (response == null) {
        if (callback) callback(response);
        return;
      }
      let messages = response.messages || [];
      for (var message of messages) {
        this.addMessage(message.text, message.category);
      }
      if (follow_redirect && response.redirect) {
        this.router.history.push(response.redirect);
      }
      if (callback) callback(response);
    };
    if (request !== undefined) {
      this.socket.emit(eventType, request, cb);
    } else {
      this.socket.emit(eventType, cb);
    }
  }

  render() {
    let { BrowserRouter, Route, Switch } = ReactRouterDOM;
    let state = this.state;

    const Root = isPartyRoot(state) ? Party : Home;

    return (
      <BrowserRouter ref={(router) => (this.router = router)}>
        <div>
          <Switch>
            <Route
              exact
              path="/"
              render={(props) => <Root state={state} {...props} />}
            />
            <Route
              exact
              path="/party"
              render={(props) => <Party state={state} {...props} />}
            />
            <Route
              exact
              path="/queue"
              render={(props) => <Home state={state} {...props} />}
            />
            <Route
              exact
              path="/appointments"
              render={(props) => <Appointments state={state} {...props} />}
            />
            <Route
              exact
              path="/online_setup"
              render={(props) => <StaffOnlineSetup state={state} {...props} />}
            />
            <Route
              path="/admin"
              render={(props) => <AdminLayout state={state} {...props} />}
            />
            <Route
              path="/activity_log"
              render={(props) => <ActivityLogLayout state={state} {...props} />}
            />
            <Route
              path="/error"
              render={(props) => <ErrorView state={state} {...props} />}
            />
            <Route
              path="/presence"
              render={(props) => <PresenceIndicator state={state} {...props} />}
            />
            <Route
              path="/tickets/:id"
              render={(props) => (
                <TicketLayout
                  state={state}
                  socket={this.socket}
                  loadTicket={this.loadTicket}
                  {...props}
                />
              )}
            />
            <Route
              path="/appointments/:id"
              render={(props) => (
                <AppointmentLayout
                  state={state}
                  socket={this.socket}
                  loadAppointment={this.loadAppointment}
                  {...props}
                />
              )}
            />
            <Route
              path="/groups/:id"
              render={(props) => (
                <PartyGroupLayout
                  state={state}
                  socket={this.socket}
                  loadGroup={this.loadGroup}
                  {...props}
                />
              )}
            />
            <Route
              path="/user/:id"
              render={(props) => <UserLayout state={state} {...props} />}
            />
            <Route
              render={(props) => (
                <ErrorView state={state} {...props} message="Page Not Found" />
              )}
            />
          </Switch>
        </div>
      </BrowserRouter>
    );
  }
}
