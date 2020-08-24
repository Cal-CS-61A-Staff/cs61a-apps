class ErrorView extends React.Component {
  componentWillMount() {
    let query = Qs.parse(this.props.location.search.substring(1));
    let state = this.props.state;

    state.message = this.props.message || query.message || 'Unknown error';
  }

  render() {
    var {Link} = ReactRouterDOM;
    let state = this.props.state;

    return (
      <div>
        <Navbar state={state} mode="error" />
        <div className="container error-view">
          <div className="row">
            <div className="col-xs-12">
              <div className="alert alert-danger">
                <p>{ state.message }</p>
              </div>
              <Link className="btn btn-primary" to="/">Home</Link>
            </div>
          </div>
        </div>
      </div>
    );
  }
}
