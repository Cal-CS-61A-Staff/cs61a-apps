import React from "react";
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

export default function Row(props) {
  let className = "Row";
  if (props.collapsed) {
    className += " closed";
  }
  if (props.childrenCollapsed !== undefined) {
    className += " pointable";
  }

  const score =
    Number.isNaN(props.score) || props.future || props.booleanValued ? (
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

        <div className="collapse show">{props.name}</div>
      </td>
      <td>
        <div className="collapse show">
          {displayedScore}
          {maxScore}
        </div>
      </td>
      {window.ENABLE_REGRADES ?
      <td>
        <div className="collapse show">
          {props.regradeable ? <>
            <a
              href="#"
              onClick={handleRegradeModalClick}
              style={{ marginLeft: "10px" }}
            >
              request
            </a>
            <RegradeRequestModal ref={regradeModalRef} assignment={props.name} email={props.email} ta={props.ta} /></> : ""}
        </div>
      </td> : "" }
    </tr>
  );
}
