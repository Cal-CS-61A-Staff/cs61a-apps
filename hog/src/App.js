// @flow
import "bootstrap/dist/css/bootstrap.min.css";
import React, { useState } from "react";
import Container from "react-bootstrap/Container";
import Navbar from "react-bootstrap/Navbar";
import Form from "react-bootstrap/Form";
import Game from "./Game";
import ResetButton from "./ResetButton";

import "./style.global.css";

export type RuleSet = {|
  "Piggy Points": boolean,
  "More Boar": boolean,
|};

export default function App() {
  const [gameKey, setGameKey] = useState(0);
  const [strategy, setStrategy] = useState(null);

  const [gameRules, setGameRules] = useState<RuleSet>({
    "Piggy Points": false,
    "More Boar": false,
  });

  const handleRestart = () => {
    setGameKey((key) => key + 1);
  };

  const handleGameRulesChange = (rule, val) => {
    setGameRules({ ...gameRules, [rule]: val });
    handleRestart();
  };

  const handleStrategyChange = (newStrategy) => {
    setStrategy(newStrategy);
    handleRestart();
  };

  return (
    <Container>
      <Navbar
        bg="dark"
        variant="dark"
        className="justify-content-between hognav"
      >
        <Navbar.Brand>
          The Game of <strong>Hog</strong>
        </Navbar.Brand>
        <Form inline>
          <ResetButton onClick={handleRestart} />
        </Form>
      </Navbar>
      <Game
        style={{ paddingTop: "10px" }}
        key={gameKey}
        strategy={strategy}
        onStrategyChange={handleStrategyChange}
        gameRules={gameRules}
        onGameRulesChange={handleGameRulesChange}
      />
    </Container>
  );
}
