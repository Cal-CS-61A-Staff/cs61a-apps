// @flow
import React from "react";
import styled from "styled-components";

const WrapperDiv = styled.div`
  text-align: center;
  width: 100%;
`;

const DiceImage = styled.img`
  width: 120px;
  height: 120px;
  margin: 10px;
`;

export default function DiceResults({ rolls }: { rolls: Array<number> }) {
  const dice = rolls.map((roll, i) => (
    <DiceImage src={"/dice_graphic.svg?num=" + roll} key={i} />
  ));
  return <WrapperDiv>{dice}</WrapperDiv>;
}
