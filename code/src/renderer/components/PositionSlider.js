import React, { useState } from "react";

export default function PositionSlider(props) {
  const [sliderPos, setSliderPos] = useState(props.value);

  return (
    <div className="pyPosSlider">
      <input
        type="range"
        min={0}
        max={props.num}
        defaultValue={sliderPos}
        step={1}
        className="pyPosSliderElem"
        onInput={props.onChange}
        onChange={() => setSliderPos(props.value)}
      />
    </div>
  );
}

// PositionSlider.propTypes = {
//     onChange: PropTypes.func,
//     value: PropTypes.number,
//     num: PropTypes.number,
// };
