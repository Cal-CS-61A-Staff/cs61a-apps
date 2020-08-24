class UpdateLocationBox extends React.Component {
    constructor(props) {
      super(props);
      this.handleChange = this.handleChange.bind(this);
      this.submit = this.submit.bind(this);
    }

    handleChange(event) {
        let {state, ticket} = this.props;
        this.newLocationId = event.target.value;
        this.setState(state); //force a re-render
    }

    submit() {
        let {state, ticket} = this.props;
        app.makeRequest('update_ticket', {
            id: ticket.id,
            location_id: this.newLocationId
        });
        this.setState(state); //force a render
    }

    render() {
        let {state, ticket} = this.props;
        let {locations} = state;
        let staff = isStaff(state);
        if (staff) {
            return null;
        }
        return (
            <div>
                <h4> If you have moved, please update your new location here:</h4>
                <div className="form-group form-group-lg">
                    <div className="input-group">
                        <SelectPicker onChange={this.handleChange} options={locations} className="selectpicker form-control" id="location" data-width="80%" data-style="btn-lg btn-default" name="location" title="Location"/>
                            <div className="input-group-btn form-right pull-left">
                                <button className="btn btn-lg btn-default" onClick={this.submit} disabled={this.newLocationId == undefined || this.newLocationId == ticket.location_id}>Update</button>
                            </div>
                    </div>
                </div>
            </div>
        );
    }
}
