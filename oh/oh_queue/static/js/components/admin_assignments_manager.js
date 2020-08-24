class AdminAssignmentsManager extends React.Component {
  render() {
    var {assignments} = this.props.state;
    return <AdminItemsManager itemName="assignment" items={assignments} />;
  }
}
