import React, { Component } from "react";
import "./ScoreEntry.css";

function valid(x) {
    return !Number.isNaN(x) && (x !== undefined);
}

export default class ScoreEntry extends Component {
    constructor(props) {
        super(props);
        this.checkboxRef = React.createRef();
    }

    componentDidMount() {
        this.postRender();
    }

    componentDidUpdate() {
        this.postRender();
    }

    handleClick = (e) => {
        e.stopPropagation();
    };

    postRender = () => {
        if (this.props.booleanValued && Number.isNaN(this.props.value)) {
            this.checkboxRef.current.indeterminate = true;
        } else if (this.props.booleanValued) {
            this.checkboxRef.current.indeterminate = false;
        }
    };

    render() {
        if (this.props.booleanValued) {
            return (
                <div className="custom-control custom-checkbox">
                    <input
                        type="checkbox"
                        ref={this.checkboxRef}
                        checked={!Number.isNaN(this.props.value)
                        && Number.parseFloat(this.props.value) !== 0}
                        className="custom-control-input"
                        onClick={this.handleClick}
                        onChange={e => !this.props.readOnly
                                && this.props.onChange(e.target.checked ? 1 : 0)
                        }
                        readOnly={this.props.readOnly}
                        id={this.props.name}
                    />
                    <label className="custom-control-label" htmlFor={this.props.name} />
                </div>
            );
        } else {
            return (
                <input
                    className="ScoreEntry"
                    type="number"
                    value={valid(this.props.value) ? this.props.value : ""}
                    placeholder={valid(this.props.placeholder) ? this.props.placeholder : ""}
                    min="0"
                    step="0.1"
                    onClick={this.handleClick}
                    onChange={e => this.props.onChange(e.target.value)}
                    readOnly={this.props.readOnly}
                />
            );
        }
    }
}
