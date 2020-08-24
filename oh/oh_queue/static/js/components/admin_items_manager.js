class AdminItemsManager extends React.Component {
  constructor(...args) {
    super(...args);

    this.state = {
      isValidInput: null,
      loading: {}
    };
    this.visibilityToggles = {};

    this.addItemInput = this.addItemInput.bind(this);
    this.editItem = this.editItem.bind(this);
    this.initializeToggle = this.initializeToggle.bind(this);
    this.renderItemInputRow = this.renderItemInputRow.bind(this);
    this.renderVisibilityToggle = this.renderVisibilityToggle.bind(this);
    this.setVisibility = this.setVisibility.bind(this);
    this.validateItemInput = this.validateItemInput.bind(this);
  }

  setVisibility(toggle) {
    var id = +toggle.dataset.itemId;
    var isVisible = toggle.checked;
    var loadingInner = "Loading...";
    this.setState({
      loading: Object.assign({}, this.state.loading, {
        [id]: true
      })
    }, () => {
      $(this.visibilityToggles[toggle.dataset.itemId]).parent().addClass('is-loading');
      $(this.visibilityToggles[toggle.dataset.itemId]).bootstrapToggle('disable');
      app.makeRequest(`update_${this.props.itemName}`, {
        id: id,
        visible: isVisible
      }, (isSuccess) => {
        var loading = Object.assign({}, this.state.loading);
        delete loading[id];
        this.setState({
          loading: loading
        });
        $(this.visibilityToggles[toggle.dataset.itemId]).parent().removeClass('is-loading');
        $(this.visibilityToggles[toggle.dataset.itemId]).bootstrapToggle('enable');
      });
    });
  }
  initializeToggle(toggle) {
    if (!toggle) return;
    var id = +toggle.dataset.itemId;
    this.visibilityToggles[id] = toggle;
    $(toggle).bootstrapToggle();
    $(toggle).change(() => this.setVisibility(toggle));
  }
  renderVisibilityToggle(item) {
    var isLoading = !item || !!this.state.loading[item.id];
    return (<input
              ref={this.initializeToggle}
              type="checkbox"
              defaultChecked={item && item.visible}
              disabled={isLoading}
              data-item-id={item ? item.id : "new"}
              data-off="Hidden"
              data-on="Visible"
              data-size="mini"
              data-toggle="toggle"
              onClick={(e) => this.setVisibility(e.target)} />);
  }

  renderItemInputRow() {
    var {isValidInput, loading} = this.state;
    var isLoading = loading.newItem;
    var innerButton = "Add";
    if (isLoading) {
      innerButton = (<div className="spinner-loading" />);
    }
    var formGroupClassNames = classNames({
      'form-group': true,
      'has-error': isValidInput === false,
      'has-success': isValidInput === true
    });

    const placeholder = this.props.itemName[0].toUpperCase() + this.props.itemName.slice(1).toLowerCase() + " Name";

    return (
      <tr key="new">
        <td className="col-md-1"></td>
        <td>
          <div className={formGroupClassNames}>
            <input ref="newItemName" className={`form-control`} type="text" minlength="1" placeholder={placeholder} disabled={isLoading} onInput={this.validateItemInput} />
          </div>
        </td>
        <td className="col-md-1">
          <button type="button" className="btn btn-default" disabled={!isValidInput || isLoading} onClick={this.addItemInput}>
            {innerButton}
          </button>
        </td>
      </tr>
    );
  }
  validateItemInput() {
    var newItemName = this.refs.newItemName;
    var name = newItemName.value;
    if (!name) {
      this.setState({
        isValidInput: null
      });
      return;
    }

    var items = this.props.items || [];
    if (items !== null && typeof items === "object" && !Array.isArray(items)) {
      items = Object.values(items);
    }
    if (items.some((item) => item.name === name)) {
      this.setState({
        isValidInput: false
      });
      return;
    }

    this.setState({
      isValidInput: true
    });
  }
  addItemInput() {
    if (this.state.isValidInput !== true) return;

    var newItemName = this.refs.newItemName;
    var name = newItemName.value;

    this.setState({
      loading: Object.assign({}, this.state.loading, {
        newItem: true
      })
    }, () => {
      app.makeRequest(`add_${this.props.itemName}`, {
        name: name
      }, (isSuccess) => {
        var loading = Object.assign({}, this.state.loading);
        delete loading.newItem;
        this.setState({
          loading: loading
        });
        if (!isSuccess || isSuccess.name !== name) return;
        newItemName.value = "";
      });
    });
  }

  editItem(e) {
    e.preventDefault();

    let input = e.target.elements[0]
    let btn = e.target.elements[1]
    var id = +input.dataset.itemId;
    this.setState({
      loading: Object.assign({}, this.state.loading, {
        [id]: true
      })
    }, () => {
      $(btn).addClass('is-loading');
      $(btn).attr('disabled', true);
      app.makeRequest(`update_${this.props.itemName}`, {
        id: id,
        name: input.value
      }, (isSuccess) => {
        var loading = Object.assign({}, this.state.loading);
        delete loading[id];
        this.setState({
          loading: loading
        });
        $(btn).removeClass('is-loading');
        $(btn).attr('disabled', false);
      });
    });

    return false;
  }

  render() {
    let { CSSTransition, TransitionGroup } = ReactTransitionGroup;

    var items = this.props.items || [];
    if (items !== null && typeof items === "object" && !Array.isArray(items)) {
      items = Object.values(items);
    }
    var itemRows = items.map((item) => {
      return (
        <tr key={item.id}>
          <td className="col-md-1">{item.id}</td>
          <td>
            <form className="form-inline" onSubmit={this.editItem}>
              <div className="form-group form-group-sm">
                <div className="input-group">
                  <input className="form-control" type="text" placeholder="New Name" data-item-id={item.id} defaultValue={item.name} />
                  <span className="input-group-btn">
                    <button className="btn btn-default btn-sm" type="submit">Edit</button>
                  </span>
                </div>
              </div>
            </form>
          </td>
          <td className="col-md-1">
            {this.renderVisibilityToggle(item)}
          </td>
        </tr>
      );
    });
    itemRows.push(this.renderItemInputRow());

    return (
      <div className="table-responsive">
        <table className="table table-hover">
          <thead>
            <tr>
              <th className="col-md-1">
                <span>ID</span>
              </th>
              <th>
                <span>Name</span>
              </th>
              <th className="col-md-1">
                <span ref={initializeTooltip} className="has-tooltip" data-toggle="tooltip" data-placement="bottom" title="Should this be visible?">Visibility</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {itemRows}
          </tbody>
        </table>
      </div>
    );
  }
}
