function Row({ title, link, prop1, prop2 }) {
    return (
        <div className="ticket-row clearfix ticket-link">
            <Link to={link} className="clearfix">
                <div className="pull-left ticket-index"/>
                <h4 className="pull-left">
                    <Link to={link}>{title}</Link>
                    <br className="visible-xs"/>
                    <small className="visible-xs ticket-status-xs">{prop2}</small>
                    <small className="visible-xs ticket-desc-xs" />
                    <small className="visible-xs ticket-created-xs">{prop1}</small>
                </h4>
                <h4 className="pull-left hidden-xs ticket-created-md"><small>{prop1}</small></h4>
                <h4 className="pull-right hidden-xs ticket-status-md "><small>{prop2}</small></h4>
            </Link>
        </div>
    )
}
