// @flow
import React from "react";
import styled from "styled-components";

const Wrapper = styled.div`
  font-size: 1.25rem;
  width: 100%;
  text-align: center;
  margin: 20px;
`;

export default function ComputerRollDisplay({
  numRolls,
}: {
  numRolls: number,
}) {
  return (
    <Wrapper>
      <p>
        It is the <b>COMPUTER&lsquo;s</b> turn.
      </p>
      <p>The computer rolls {numRolls} dice.</p>
    </Wrapper>
  );
}
