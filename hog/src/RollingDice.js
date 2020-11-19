// @flow
import React, { useState } from "react";
import DiceResults from "./DiceResults";
import { useInterval } from "./utils";

export default function RollingDice({ numRolls }: { numRolls: number }) {
  const randomRolls = () =>
    Array(numRolls)
      .fill()
      .map(() => Math.floor(Math.random() * 6) + 1);

  const [rolls, setRolls] = useState(randomRolls);

  useInterval(() => {
    setRolls(randomRolls);
  }, 200);

  return <DiceResults rolls={rolls} />;
}
