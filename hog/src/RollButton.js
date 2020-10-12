// @flow
import React, { useState } from "react";
import Button from "react-bootstrap/Button";
import styled from "styled-components";
import { numberStrings } from "./constants";
import ResetButton from "./ResetButton";

const Wrapper = styled.div`
    font-size: 1.25rem;
    width: 100%;
    text-align: center;
    margin: 20px;
`;

type Props = {|
    playerIndex: number, freeBacon: boolean, onClick: (number) => mixed, onRestart: () => mixed
|};

export default function RollButton({
    playerIndex, freeBacon, onClick, onRestart,
} : Props) {
    const min = freeBacon ? 0 : 1;

    const [numberOfRolls, setNumberOfRolls] = useState(min);

    const handleChange = (e) => {
        const val = Math.max(Math.min(10, e.target.value), min);
        setNumberOfRolls(e.target.value && val);
    };

    const handleClick = () => {
        onClick(numberOfRolls);
    };

    return (
        <Wrapper>
            <p>
                It is Player
                {" "}
                <b>
                    {numberStrings[playerIndex]}
                    &lsquo;s
                </b>
                {" "}
                turn.
            </p>
            <p>
                Roll
                {" "}
                <input type="number" min={min} max={10} value={numberOfRolls} onChange={handleChange} />
                {" "}
            Dice.
            </p>
            <p>
                <Button variant={["primary", "warning"][playerIndex]} size="lg" onClick={handleClick}> Roll!</Button>
            </p>
            <p>
                <ResetButton onClick={onRestart} />
            </p>
        </Wrapper>
    );
}
