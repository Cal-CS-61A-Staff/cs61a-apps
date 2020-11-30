import React, { useState } from "react";

import "./CaptchaChallenge.css";
import Indicator from "./Indicator";
import Input from "./Input";
import post from "./post";
import { formatNum, getCurrTime, useInterval } from "./utils";

export default function CaptchaChallenge({ images, lastWordLen, onSubmit }) {
  const [typedWords, setTypedWords] = useState([]);
  const [currWord, setCurrWord] = useState("");
  const [startTime] = useState(getCurrTime());
  const [wpm, setWPM] = useState(null);
  const [active, setActive] = useState(true);

  const updateWPM = async (word) => {
    const text = typedWords.join(" ");
    const { wpm: newWPM } = await post("/analyze", {
      promptedText: text,
      typedText: text,
      startTime,
      endTime: getCurrTime(),
    });
    setWPM(newWPM);
    setCurrWord(word);
    if (
      typedWords.length + 1 === images.length &&
      word &&
      word.length === lastWordLen
    ) {
      setTypedWords(typedWords.concat([word]));
      setCurrWord("");
      setActive(false);
      onSubmit(typedWords.concat([word]));
    }
  };

  useInterval(updateWPM, 100);

  const onWordTyped = (word) => {
    if (word === "") {
      return true;
    }
    setCurrWord("");
    setTypedWords(typedWords.concat([word]));
    return true;
  };

  const handleSubmit = () => {
    onSubmit(typedWords.concat([currWord]));
  };

  const popPrevWord = () => {
    if (typedWords.length) {
      setTypedWords(typedWords.slice(0, typedWords.length - 1));
      return typedWords[typedWords.length - 1];
    } else {
      return "";
    }
  };

  return (
    <div className="CaptchaChallenge">
      Look at the following words:
      <div className="images">
        {/* eslint-disable-next-line jsx-a11y/alt-text */}
        {images.map((image, i) => (
          <img
            className={i === typedWords.length ? "activeImage" : ""}
            src={image}
            key={i}
          />
        ))}
      </div>
      <br />
      <Input
        correctWords={typedWords}
        words={typedWords}
        onWordTyped={onWordTyped}
        onChange={updateWPM}
        popPrevWord={popPrevWord}
        active={active}
      />
      <br />
      <div className="form-group">
        <button
          onClick={handleSubmit}
          type="submit"
          className="btn btn-primary"
        >
          Submit
        </button>
        <Indicator text={`WPM: ${formatNum(wpm)}`} />
      </div>
    </div>
  );
}
