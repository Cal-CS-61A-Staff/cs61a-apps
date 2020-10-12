import React from "react";
import styled from "styled-components";

const StyledDiv = styled.code`
    white-space: pre-line;
    width: 100%;
    text-align: center;
    border: 2px solid black;
    padding: 10px;
    margin-top: 10px;
`;

export default function Commentary({ text } : { text: string }) {
    return text && (
        <StyledDiv>
            {text}
        </StyledDiv>
    );
}
