function MyAssignedTickets({ state, tickets }) {
    return !!tickets.length && <div>
        <div className="assigned-tickets-header">
            Your Assigned Tickets
        </div>
        {tickets.map(ticket => <Ticket key={ticket.id} state={state} ticket={ticket} independent />)}
    </div>;
}
