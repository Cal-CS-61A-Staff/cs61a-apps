// @flow
import React from "react";
import styled from "styled-components";
import { numberStrings } from "./constants";

const OuterDiv = styled.div`
  width: 150px;
  border: solid black 2px;
  font-weight: bold;
  text-align: center;
  display: flex;
  flex-direction: column;
`;

const ScoreDiv = styled.div`
  width: 100%;
  height: 130px;
  line-height: 130px;
  font-size: 48pt;
  background: ${(props) => (props.isCurrent ? "white" : "transparent")};
`;

const PlayerDiv = styled.div`
  width: 100%;
  line-height: 30px;
  background: ${(props) => (props.isCurrent ? "#17a2b8" : "grey")};
  color: white;
`;

type Props = { score: number, playerIndex: number, currentPlayer: number };

export default function ScoreIndicator({
  score,
  playerIndex,
  currentPlayer,
}: Props) {
  const isCurrent = currentPlayer === playerIndex;
  return (
    <OuterDiv>
      <ScoreDiv isCurrent={isCurrent}>{score}</ScoreDiv>
      <PlayerDiv isCurrent={isCurrent}>
        {isCurrent ? "➜ " : ""}
        Player {numberStrings[playerIndex]}
      </PlayerDiv>
    </OuterDiv>
  );
}
