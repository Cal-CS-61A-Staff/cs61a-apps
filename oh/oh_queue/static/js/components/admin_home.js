class AdminHome extends React.Component {
  render() {
    return (
      <div className="jumbotron blue">
        <div className="container">
          <section className="page-header">
            <div className="row">
              <div className="col-md-12">
                <h1>{window.courseName} Admin Panel</h1>
                <h2>Edit assignments, locations, and more!</h2>
                <p>Found a bug? Want to change something? Talk to us at <a href="https://github.com/Cal-CS-61A-Staff/oh-queue">our GitHub repo</a>!</p>
              </div>
            </div>
          </section>
        </div>
      </div>
    );
  }
}
