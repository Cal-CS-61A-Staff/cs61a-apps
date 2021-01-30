// @flow
import React, { useState } from "react";
import Button from "react-bootstrap/Button";
import styled from "styled-components";
import { numberStrings } from "./constants";

const Wrapper = styled.div`
  font-size: 1.25rem;
  width: 100%;
  text-align: center;
  margin-top: 20px;
`;

type Props = {|
  playerIndex: number,
  piggyPoints: boolean,
  onClick: (number) => mixed,
|};

export default function RollButton({
  playerIndex,
  piggyPoints,
  onClick,
}: Props) {
  const min = piggyPoints ? 0 : 1;

  const [numberOfRolls, setNumberOfRolls] = useState(min);

  const handleChange = (e) => {
    const val = Math.max(Math.min(10, e.target.value), min);
    setNumberOfRolls(e.target.value && val);
  };

  const handleClick = () => {
    onClick(numberOfRolls);
  };

  return (
    <Wrapper>
      <p>
        It is Player{" "}
        <b>
          {numberStrings[playerIndex]}
          &lsquo;s
        </b>{" "}
        turn.
      </p>
      <p>
        Roll{" "}
        <input
          type="number"
          min={min}
          max={10}
          value={numberOfRolls}
          onChange={handleChange}
        />{" "}
        Dice.
        <Button
          variant="info"
          size="lg"
          style={{ marginLeft: "10px" }}
          onClick={handleClick}
        >
          {" "}
          Roll!
        </Button>
      </p>
      <p></p>
    </Wrapper>
  );
}
