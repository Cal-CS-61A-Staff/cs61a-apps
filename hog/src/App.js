// @flow
import "bootstrap/dist/css/bootstrap.min.css";
import React, { useState } from "react";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import styled from "styled-components";
import Game from "./Game";

import "./style.global.css";

const CenteredDiv = styled.div`
    text-align: center;
    margin-top: 10px;
    font-weight: bold;
`;

export type RuleSet = {|
    "Free Bacon": boolean,
    "Swine Align": boolean,
    "Pig Pass": boolean,
|};

export default function App() {
    const [gameKey, setGameKey] = useState(0);
    const [strategy, setStrategy] = useState(null);

    const [gameRules, setGameRules] = useState<RuleSet>({
        "Free Bacon": false,
        "Swine Align": true,
        "Pig Pass": false,
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
            <Row>
                <Col>
                    <CenteredDiv>
                        <h1 className="display-4">
                            The Game of
                            {" "}
                            <b>Hog.</b>
                        </h1>
                    </CenteredDiv>
                </Col>
            </Row>
            <Game
                key={gameKey}
                strategy={strategy}
                onRestart={handleRestart}
                onStrategyChange={handleStrategyChange}
                gameRules={gameRules}
                onGameRulesChange={handleGameRulesChange}
            />
        </Container>
    );
}
