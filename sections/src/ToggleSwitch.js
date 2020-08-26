/* @flow strict

Note that this component relies on jQuery being exposed as a global.
For CRA apps, include a script tab in public/index.html importing jQuery
from a CDN. (slim,minified works)

*/
import * as React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import "bootstrap4-toggle";
import "bootstrap4-toggle/css/bootstrap4-toggle.min.css";

type Props = {
  defaultChecked: boolean,
  onChange: (boolean) => void,
  offText?: ?string,
  onText?: ?string,
};

export default function ToggleSwitch({
  defaultChecked,
  onChange,
  offText,
  onText,
}: Props) {
  const [initialized, setInitialized] = useState(false);
  const toggleRef = useRef();

  const handleClick = useCallback(
    (toggle: HTMLInputElement) => {
      onChange(toggle.checked);
    },
    [onChange]
  );

  const initializeToggle = (toggle) => {
    if (toggle == null || initialized) return;
    window.$(toggle).bootstrapToggle();
    window.$(toggle).change(() => handleClick(toggle));
    setInitialized(true);
    toggleRef.current = toggle;
  };

  useEffect(() => {
    const currToggle = toggleRef.current;
    if (currToggle != null) {
      window.$(currToggle).off("change");
      window.$(currToggle).bootstrapToggle(defaultChecked ? "on" : "off");
      window.$(currToggle).change(() => handleClick(currToggle));
    }
  }, [defaultChecked, handleClick]);

  return (
    <input
      ref={initializeToggle}
      type="checkbox"
      defaultChecked={defaultChecked}
      data-off={offText}
      data-on={onText}
      data-size="mini"
      data-toggle="toggle"
      onClick={handleClick}
    />
  );
}
