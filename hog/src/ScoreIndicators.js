// @flow
import React from "react";
import styled from "styled-components";
import ScoreIndicator from "./ScoreIndicator";

const Wrapper = styled.div`
  display: flex;
  justify-content: space-evenly;
`;

export default function ScoreIndicators({
  scores,
  currentPlayer,
}: {
  scores: $ReadOnlyArray<number>,
}) {
  return (
    <Wrapper>
      {scores.map((score, i) => (
        <ScoreIndicator
          key={i}
          score={score}
          playerIndex={i}
          currentPlayer={currentPlayer}
        />
      ))}
    </Wrapper>
  );
}
