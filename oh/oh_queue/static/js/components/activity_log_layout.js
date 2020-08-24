function ActivityLogLayout({ state }) {
    const [activeTab, setActiveTab] = React.useState(0);

    const [userList, setUserList] = React.useState([]);
    const [isLoading, setIsLoading] = React.useState(false);

    const [searchText, setSearchText] = React.useState("");

    if (state.currentUser && !state.currentUser.isStaff) {
        const { Redirect } = ReactRouterDOM;
        return <Redirect to={`user/${state.currentUser.id}`} />;
    }

    if (app && !isLoading && userList.length === 0) {
        setIsLoading(true);
        app.makeRequest("list_users", null, false, (users) => {
            setUserList(users);
        })
    }

    const foundUsers = userList.filter(
        ({ name, email }) => (name + email).toLowerCase().includes(searchText.toLowerCase())
    );

    return (
        <div>
            <Navbar state={state} mode="activity_log"/>
            <OfflineIndicator offline={state.offline && state.loaded}/>
            <div className="jumbotron">
                <div className="container">
                    <h2> Activity Log </h2>
                    <p>View the activity of any user of the queue.</p>
                    <div className="form-group">
                        <form>
                            <div className="input-group appointment-input">
                                <input
                                    className="form-control"
                                    required="required"
                                    placeholder="Search for a student or a member of staff"
                                    value={searchText}
                                    onChange={e => setSearchText(e.target.value)}
                                />
                                <span className="input-group-btn">
                                    <button className="btn btn-default" type="button">
                                        Search
                                    </button>
                                </span>
                            </div>
                        </form>

                    </div>
                    <div className="activity-buttons">
                        <Link to={`/user/${state.currentUser && state.currentUser.id}`} className="btn btn-primary">
                            My activity
                        </Link>
                        <Link className="btn btn-warning">Class Overview</Link>
                    </div>
                </div>
            </div>

            <div className="container">
                <Messages messages={state.messages}/>

                {searchText ?
                    (
                        <Tabs selectedIndex={0} onClick={() => null}>
                            <Tab label={`Search Results (${foundUsers.length})`}>
                                <UserList users={foundUsers} />
                            </Tab>
                        </Tabs>
                    ) :
                    (
                        <Tabs selectedIndex={activeTab} onSelect={setActiveTab}>
                            <Tab label="Staff">
                                <UserList users={userList.filter(({ isStaff }) => isStaff)} />
                            </Tab>
                            <Tab label="Students">
                                <UserList users={userList.filter(({ isStaff }) => !isStaff)} />
                            </Tab>
                        </Tabs>
                    )}
            </div>
        </div>
    );
}

function UserList({ users }) {
    return (
        <div className="queue">
            {users.map(user => <User user={user}/>)}
        </div>
    )
}

function User({ user }) {
    return (
        <Row
            title={user.name}
            link={`/user/${user.id}`}
            prop1={user.email}
            prop2={`Role: ${user.isStaff ? "Staff" : "Student"}`}
        />
    )
}
