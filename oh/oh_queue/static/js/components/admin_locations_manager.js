class AdminLocationsManager extends React.Component {
  render() {
    var {locations} = this.props.state;
    return (
        <AdminItemsManager
            itemName="location"
            items={Object.values(locations).filter(({ name }) => name !== "Online")}
        />
    );
  }
}
