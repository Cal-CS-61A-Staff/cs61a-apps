// @flow
import React, { useState } from "react";

import FormControl from "react-bootstrap/FormControl";
import InputGroup from "react-bootstrap/InputGroup";
import styled from "styled-components";

const StyledDiv = styled.div`
  margin-top: 15px;
`;

type Props = { strategy: ?string, onStrategyChange: (?string) => mixed };

export default function StrategyPicker({ strategy, onStrategyChange }: Props) {
  const defaultString = "Pick a strategy";
  const displayStrategy = strategy || defaultString;
  const [selected, setSelected] = useState(displayStrategy);

  const handleClick = (e) => {
    if (e.target.checked) {
      onStrategyChange(selected);
    } else {
      onStrategyChange(null);
    }
  };

  const handleSelect = (e) => {
    setSelected(e.target.value);
    onStrategyChange(e.target.value);
  };

  return (
    <StyledDiv>
      <h5>Play against the computer:</h5>
      <InputGroup className="mb-3">
        <InputGroup.Prepend>
          <InputGroup.Checkbox
            aria-label="Checkbox for following text input"
            checked={!!strategy}
            onChange={handleClick}
          />
        </InputGroup.Prepend>
        <FormControl as="select" onChange={handleSelect} value={selected}>
          <option disabled hidden>
            {defaultString}
          </option>
          <option>piggypoints_strategy</option>
          <option>more_boar_strategy</option>
          <option>final_strategy</option>
        </FormControl>
      </InputGroup>
    </StyledDiv>
  );
}
