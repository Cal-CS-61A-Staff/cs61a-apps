class SelectPicker extends React.Component {
  constructor(...args) {
    super(...args);

    this.refreshSelect = this.refreshSelect.bind(this);
  }
  componentDidMount() {
    this.refreshSelect();
  }
  refreshSelect() {
    $(this.refs.selectpicker).selectpicker('refresh');
  }
  componentDidUpdate() {
    this.refreshSelect();
  }
  render() {
    var {options, emptyOption} = this.props;
    if (options && !Array.isArray(options) && typeof options === "object") {
      options = Object.entries(options).map((entry) => Object.assign({}, {
        id: entry[0]
      }, entry[1]));
    }
    var optionsElements = null;
    if (options) {
      optionsElements = options.map((obj) => {
        if (typeof obj === "string") {
          return (<option key={obj} value={obj}>{obj}</option>)
        } else if (obj.id !== undefined && obj.name !== undefined) {
          return (<option key={obj.id} value={obj.id}>{obj.name}</option>)
        } else {
          let str = JSON.stringify(obj);
          return (<option key={str} value={str}>{str}</option>)
        }
      }).filter((option) => option);
    }
    var props = Object.assign({}, this.props);
    delete props.emptyOption;
    delete props.options;
    return (
      <select ref="selectpicker" {...props}>
        {emptyOption && <option value="">{emptyOption}</option>}
        {optionsElements}
      </select>
    );
  }
}
