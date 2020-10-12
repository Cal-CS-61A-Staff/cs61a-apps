// @flow
import React from "react";
import styled from "styled-components";

import d1 from "./dice_imgs/die1.gif";
import d2 from "./dice_imgs/die2.gif";
import d3 from "./dice_imgs/die3.gif";
import d4 from "./dice_imgs/die4.gif";
import d5 from "./dice_imgs/die5.gif";
import d6 from "./dice_imgs/die6.gif";

const diceImgs = [d1, d2, d3, d4, d5, d6];

const WrapperDiv = styled.div`
    text-align: center;
    width: 100%;
`;

const DiceImage = styled.img`
    width: 120px;
    height: 120px;
    border: 1px solid black;
    margin: 10px;
`;

export default function DiceResults({ rolls } : {rolls: Array<number> }) {
    const dice = rolls.map((roll, i) => <DiceImage src={diceImgs[roll - 1]} key={i} />);
    return (
        <WrapperDiv>
            {dice}
        </WrapperDiv>
    );
}
