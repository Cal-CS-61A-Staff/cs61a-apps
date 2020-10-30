// @flow
import React from "react";
import styled from "styled-components";
import { bgColors, colors, numberStrings } from "./constants";

const OuterDiv = styled.div`
    width: 150px;
    border: solid black 2px;
    font-weight: bold;
    text-align: center;
`;

const ScoreDiv = styled.div`
    width: 100%;
    height: 130px;
    line-height: 130px;
    font-size: 48pt;
`;

const PlayerDiv = styled.div`
    width: 100%;
    height: 30px;
    line-height: 30px;
    background: ${({ playerIndex }) => bgColors[playerIndex]};
    color: ${({ playerIndex }) => colors[playerIndex]};
`;

type Props = {score: number, playerIndex: number};

export default function ScoreIndicator({ score, playerIndex } : Props) {
    return (
        <OuterDiv>
            <ScoreDiv>
                {score}
            </ScoreDiv>
            <PlayerDiv playerIndex={playerIndex}>
                Player
                {" "}
                {numberStrings[playerIndex]}
            </PlayerDiv>
        </OuterDiv>
    );
}
