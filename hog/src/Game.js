// @flow
import React, { useRef, useState } from "react";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import type { RuleSet } from "./App";
import ComputerRollDisplay from "./ComputerRollDisplay";
import GameOptions from "./GameOptions";
import StrategyPicker from "./StrategyPicker";
import Commentary from "./Commentary";
import DiceResults from "./DiceResults";

import post from "./post";
import RollButton from "./RollButton";
import RollingDice from "./RollingDice";
import ScoreIndicators from "./ScoreIndicators";
import { wait } from "./utils";
import VictoryScreen from "./VictoryScreen";

const states = {
  WAITING_FOR_INPUT: "WAITING_FOR_INPUT",
  DISPLAYING_COMPUTER_MOVE: "DISPLAYING_COMPUTER_MOVE",
  ROLLING_DICE: "ROLLING_DICE",
  DISPLAYING_CHANGE: "DISPLAYING_CHANGE",
  GAME_OVER: "GAME_OVER",
};

const goal = 100;

type State = $Keys<typeof states>;

type Props = {
  onRestart: () => mixed,
  strategy: ?string,
  onStrategyChange: (?string) => mixed,
  gameRules: RuleSet,
  onGameRulesChange: (string, boolean) => mixed,
};

export default function Game({
  onRestart,
  strategy,
  onStrategyChange,
  gameRules,
  onGameRulesChange,
}: Props) {
  const [state, setState] = useState<State>(states.WAITING_FOR_INPUT);
  const [displayedRolls, setDisplayedRolls] = useState<number[]>([]);
  const [playerIndex, setPlayerIndex] = useState(0);
  const [scores, setScores] = useState<[number, number]>([0, 0]);
  const [numRolls, setNumRolls] = useState<number>(0);
  const [messages, setMessages] = useState<[string]>([]);

  const moveHistory = useRef([]);
  const rollHistory = useRef([]);

  const handleRoll = async (inputNumRolls, currPlayerIndex = playerIndex) => {
    setState(states.ROLLING_DICE);
    setNumRolls(inputNumRolls);
    moveHistory.current.push(inputNumRolls);
    const [{ message, rolls, finalScores, who }] = await Promise.all([
      post("/take_turn", {
        prevRolls: rollHistory.current,
        moveHistory: moveHistory.current,
        goal,
        gameRules,
      }),
      ...[inputNumRolls && wait(1000)],
    ]);
    setDisplayedRolls(rolls.slice(rollHistory.current.length));
    setScores(finalScores);
    setState(states.DISPLAYING_CHANGE);
    const messages = [];
    if (who === currPlayerIndex) {
      messages.push(`More boar! Extra turn granted to Player ${who}`);
    }
    message && messages.push(message);
    setMessages(messages);
    rollHistory.current = rolls;
    strategy && (await wait(2500));

    setPlayerIndex(who);
    if (Math.max(...finalScores) >= goal) {
      setState(states.GAME_OVER);
    } else if (who === 1 && strategy) {
      const nextMove = await post("/strategy", { name: strategy, scores });
      setNumRolls(nextMove);
      setState(states.DISPLAYING_COMPUTER_MOVE);
      await wait(2500);
      return handleRoll(nextMove, who);
    } else {
      setState(states.WAITING_FOR_INPUT);
    }
  };

  const diceDisplay = {
    [states.WAITING_FOR_INPUT]: <DiceResults rolls={displayedRolls} />,
    [states.ROLLING_DICE]: <RollingDice numRolls={numRolls} />,
    [states.DISPLAYING_CHANGE]: <DiceResults rolls={displayedRolls} />,
    [states.GAME_OVER]: null,
    [states.DISPLAYING_COMPUTER_MOVE]: (
      <ComputerRollDisplay numRolls={numRolls} />
    ),
  }[state];

  return (
    <>
      <Row>
        <Col>
          <ScoreIndicators scores={scores} currentPlayer={playerIndex} />
        </Col>
      </Row>
      {state !== states.DISPLAYING_COMPUTER_MOVE && (
        <Row>
          <RollButton
            playerIndex={playerIndex}
            piggyPoints={gameRules["Piggy Points"]}
            onClick={handleRoll}
          />
        </Row>
      )}
      <Row>
        <Col>{diceDisplay}</Col>
      </Row>
      <Row>
        <Col>
          <Commentary messages={messages} />
        </Col>
      </Row>
      {state === states.GAME_OVER && (
        <VictoryScreen
          winner={scores[0] > scores[1] ? 0 : 1}
          onRestart={onRestart}
          onStrategyChange={onStrategyChange}
        />
      )}
      {state === states.WAITING_FOR_INPUT && (
        <>
          <Row>
            <Col>
              <GameOptions
                gameRules={gameRules}
                onGameRulesChange={onGameRulesChange}
              />
            </Col>
          </Row>
          <Row>
            <Col>
              <StrategyPicker
                strategy={strategy}
                onStrategyChange={onStrategyChange}
              />
            </Col>
          </Row>
        </>
      )}
    </>
  );
}
