// @flow
import React from "react";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import styled from "styled-components";
import StrategyPicker from "./StrategyPicker";
import { bgColors, colors, numberStrings } from "./constants";
import ResetButton from "./ResetButton";

const CenteredDiv = styled.div`
  text-align: center;
  margin-top: 30px;
  font-weight: bold;
  font-size: 24px;
  width: 100%;
  color: ${({ color }) => color};
  background: ${({ bgColor }) => bgColor};
  padding: 5px;
`;

const Wrapper = styled.div`
  font-size: 1.25rem;
  width: 100%;
  text-align: center;
  margin: 20px;
`;

type Props = {|
  winner: number,
  onRestart: () => mixed,
  onStrategyChange: (?string) => mixed,
|};

export default function VictoryScreen({
  winner,
  onRestart,
  onStrategyChange,
}: Props) {
  return (
    <>
      <Row>
        <CenteredDiv color={colors[winner]} bgColor={bgColors[winner]}>
          Player {numberStrings[winner]} has won! Congratulations!
        </CenteredDiv>
      </Row>
      <Row>
        <Wrapper>
          <ResetButton onClick={onRestart} />
        </Wrapper>
      </Row>
      <Row>
        <Col>
          <StrategyPicker strategy={null} onStrategyChange={onStrategyChange} />
        </Col>
      </Row>
    </>
  );
}
