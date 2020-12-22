import React, { useState, useRef } from "react";
import { CopyToClipboard } from "react-copy-to-clipboard";
import $ from "jquery";

import { Textfit } from "react-textfit";

import "./GeneratedCommand.css";

export default function GeneratedCommand(props) {
  const [copyText, setCopyText] = useState("Copy");

  const sensor = useRef();
  const ref = useRef();

  let generated = "python3 ok";
  if (props.options) {
    for (const option of props.options.mandatoryArgs) {
      if (option.shortForm) {
        generated += ` -${option.shortForm}`;
      } else {
        generated += ` --${option.longForm}`;
      }
    }
    for (const option of props.options.optionalArgs) {
      if (props.selectedArgs[option.longForm]) {
        if (option.shortForm) {
          generated += ` -${option.shortForm}`;
        } else {
          generated += ` --${option.longForm}`;
        }
        if (option.isValue) {
          generated += ` ${props.selectedArgs[option.longForm]}`;
        }
      }
    }
  }

  function stickTop() {
    const windowTop = $(window).scrollTop();
    const { top } = $(sensor.current).offset();
    if (windowTop > top) {
      $(sensor.current).height($(ref.current).outerHeight());
      $(ref.current).addClass("sticky");
    } else {
      $(ref.current).removeClass("sticky");
      $(sensor.current).height(0);
    }
  }

  $(window).scroll(stickTop);

  return (
    <>
      <div ref={sensor} />
      <div className="row" ref={ref}>
        <div className="col">
          <div className="GeneratedCommand">
            <div className="Command">
              <Textfit mode="single" forceSingleModeWidth={false} max={28}>
                <code>{generated}</code>
              </Textfit>
            </div>
            <div className="CopyButtonContainer">
              <CopyToClipboard
                text={generated}
                onCopy={() => {
                  setCopyText("Copied!");
                  setTimeout(() => {
                    setCopyText("Copy");
                  }, 1000);
                  document.activeElement.blur();
                }}
              >
                <button className="btn btn-primary CopyButton" type="button">
                  <span>{copyText}</span>
                </button>
              </CopyToClipboard>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
