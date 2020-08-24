class FilterControls extends React.Component {
  constructor(props) {
    super(props);

    this.updateFilter = this.updateFilter.bind(this);
  }

  updateFilter() {
    app.setFilter({
      assignment_id: $('#assignment').val(),
      location_id: $('#location').val(),
      question: $('#question').val(),
    });
  }

  render() {
    let {filter, state} = this.props;
    let {assignments, locations} = state;

    let filteredAssignments = Object.values(assignments).sort((a, b) => a.name.localeCompare(b.name));
    let filteredLocations = Object.values(locations).sort((a, b) => a.name.localeCompare(b.name));

    return (
      <div className="row form-group form-group-lg">
        <div className="col-xs-12 col-sm-4 filter-field">
          <SelectPicker options={filteredAssignments} emptyOption="Any Assignment" className="selectpicker form-control" data-live-search="true" data-size="8" data-width="100%" data-style="btn-lg btn-default" id="assignment" name="assignment" title="Assignment" onChange={this.updateFilter}/>
        </div>
        <div className="col-xs-12 col-sm-4 filter-field">
          <input className="form-control" type="text" id="question" name="question" title="Question" placeholder="Question" onChange={this.updateFilter}/>
        </div>
        <div className="col-xs-12 col-sm-4 filter-field">
          <SelectPicker options={filteredLocations} emptyOption="Any Location" className="selectpicker form-control" id="location" data-width="100%" data-style="btn-lg btn-default" name="location" title="Location" onChange={this.updateFilter}/>
        </div>
        <hr></hr>
      </div>
    );
  }
};
