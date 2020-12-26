import * as React from "react";
import NavButton from "./NavButton.js";
import PositionSlider from "./PositionSlider.js";

// PositionChooser.propTypes = {
//     onChange: PropTypes.func,
//     value: PropTypes.number,
//     num: PropTypes.number,
// };

export default class PositionChooser extends React.Component {
  handlePrevClick = () => {
    this.props.onChange(Math.max(this.props.value - 1, 0));
  };

  handleNextClick = () => {
    this.props.onChange(Math.min(this.props.value + 1, this.props.num));
  };

  handleDrag = (e) => {
    this.props.onChange(parseInt(e.target.value, 10));
  };

  render() {
    return (
      <div className="pyPosChooser">
        <NavButton prev onClick={this.handlePrevClick} />
        <PositionSlider
          num={this.props.num}
          value={this.props.value}
          onChange={this.handleDrag}
        />
        <NavButton next onClick={this.handleNextClick} />
      </div>
    );
  }
}
