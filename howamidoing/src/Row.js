import React, { Component } from "react";
import "./Row.css";
import ScoreEntry from "./ScoreEntry.js";

import $ from "jquery";
import RegradeRequestModal from "./RegradeRequestModal.js";

function formatScore(score, places = 2) {
  if (Number.isNaN(parseFloat(score))) {
    return score;
  }
  return Number.parseFloat(score).toFixed(places);
}

class Row extends Component {
  constructor(props) {
    super(props);
    this.state = {
      regradeable: false,
    };
  }

  checkRegradeable = async (target) => {
    if (this.props.regradeable) {
      const location = `./canRegrade?name=${this.props.name}&email=${this.props.email}`;
      const { canRegrade } = await $.getJSON(location, { target });
      console.log(`can regrade ${this.props.name}? ${canRegrade}`);
      this.setState({
        regradeable: canRegrade,
      });
    } else {
      this.setState({
        regradeable: false,
      });
    }
  };

  componentDidMount() {
    return this.checkRegradeable();
  }

  render() {
    const props = this.props;
    let className = "Row";
    if (props.collapsed) {
      className += " closed";
    }
    if (props.childrenCollapsed !== undefined) {
      className += " pointable";
    }

    let displayData = props.customDisplay && props.customDisplay(props);
    let displayName =
      displayData && displayData.name ? displayData.name : props.name;
    let description = displayData && displayData.description;

    const score =
      // 0 is a valid score
      displayData && displayData.score !== undefined ? (
        String(displayData.score)
      ) : Number.isNaN(props.score) || props.future || props.booleanValued ? (
        <ScoreEntry
          name={props.name}
          value={props.plannedScore}
          placeholder={props.placeholder}
          readOnly={props.readOnly}
          onChange={(val) =>
            props.booleanValued
              ? props.onChange(props.name, val * props.maxScore)
              : props.onChange(props.name, val)
          }
          booleanValued={props.booleanValued}
        />
      ) : (
        formatScore(props.score)
      );

    const maxScore =
      !props.booleanValued && props.maxScore && Number.isFinite(props.maxScore)
        ? ` / ${formatScore(props.maxScore)}`
        : "";

    const displayedScore = !props.noScore && score;

    const regradeModalRef = React.createRef();
    const handleRegradeModalClick = () => {
      $(regradeModalRef.current).modal();
    };
    return (
      <tr
        onClick={props.onClick}
        className={className}
        style={{ color: props.hidden ? "gray" : "black" }}
      >
        <td style={{ paddingLeft: 10 + 40 * props.indent }}>
          {props.childrenCollapsed !== undefined ? (
            <button
              type="button"
              className="close closeButton"
              aria-label="Close"
            >
              <span aria-hidden="true">
                {props.childrenCollapsed ? "+" : "-"}
              </span>
            </button>
          ) : (
            false
          )}

          <div
            className="collapse show d-inline-block"
            style={{ whiteSpace: "pre-wrap" }}
          >
            {displayName}
            {!props.childrenCollapsed ? (
              <>
                <br />
                {description}
              </>
            ) : (
              false
            )}
          </div>
        </td>
        <td>
          <div className="collapse show">
            {displayedScore}
            {maxScore}
          </div>
        </td>
        {window.ENABLE_REGRADES ? (
          <td>
            <div className="collapse show">
              {this.state.regradeable ? (
                <>
                  <a
                    href="#"
                    onClick={handleRegradeModalClick}
                    style={{ marginLeft: "10px" }}
                  >
                    <i className="fa fa-external-link"></i>
                  </a>
                  <RegradeRequestModal
                    ref={regradeModalRef}
                    assignment={props.name}
                    email={props.email}
                    ta={props.ta}
                  />
                </>
              ) : (
                ""
              )}
            </div>
          </td>
        ) : (
          ""
        )}
      </tr>
    );
  }
}
export default Row;
