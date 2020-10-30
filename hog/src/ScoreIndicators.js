// @flow
import React from "react";
import styled from "styled-components";
import ScoreIndicator from "./ScoreIndicator";

const Wrapper = styled.div`
    display: flex;
    justify-content: space-evenly;
`;

export default function ScoreIndicators({ scores } : {scores: $ReadOnlyArray<number>}) {
    return (
        <Wrapper>
            {scores.map((score, i) => <ScoreIndicator score={score} key={i} playerIndex={i} />) }
        </Wrapper>
    );
}
