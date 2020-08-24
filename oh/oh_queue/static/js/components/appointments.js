function Appointments({ state }) {
    const { Redirect } = ReactRouterDOM;

    if (!state.loaded) return null;

    if (!state.currentUser) {
        return <Redirect to="/" />
    }
    return (
        <div className="admin-root">
            <Navbar state={state} mode="appointments"/>
            <OfflineIndicator offline={state.offline && state.loaded}/>
            <FutureSlots state={state} />
        </div>
    );
}
