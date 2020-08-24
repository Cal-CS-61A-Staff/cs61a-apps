class DescriptionBox extends React.Component {
  render() {
    let {locked, state, ticket, prompt, placeholder} = this.props;
    let staff = isStaff(state);

    if (staff || locked) {
      return (
        <p className="ticket-view-desc">{ticket.description ? ticket.description : <i>No description</i>}</p>
      );
    } else {
      return (
        <div>
          <h4>{prompt}</h4>
          <textarea className="description-box" value={this.props.description} onChange={e => this.props.onChange(e.target.value)}
          rows="5" placeholder={placeholder}  />
          {this.props.description !== ticket.description ? <button onClick={this.props.onSubmit} className="description-button btn btn-default btn-lg btn-block"> Save Description </button> : null}
        </div>
      );
    }
  }
}
