// @flow
import React from "react";
import Form from "react-bootstrap/Form";

import styled from "styled-components";
import type { RuleSet } from "./App";

const StyledDiv = styled.div`
  margin-top: 15px;
`;

type Props = {
  gameRules: RuleSet,
  onGameRulesChange: (string, boolean) => mixed,
};

export default function GameOptions({ gameRules, onGameRulesChange }: Props) {
  return (
    <StyledDiv>
      <h5>Enable game rules:</h5>
      {Object.entries(gameRules).map(([rule, state]) => (
        <Form.Check
          key={rule}
          custom
          inline
          type="switch"
          id={`rule-checkbox-${rule}`}
          checked={state}
          label={rule}
          onChange={() => onGameRulesChange(rule, !state)}
        />
      ))}
    </StyledDiv>
  );
}
