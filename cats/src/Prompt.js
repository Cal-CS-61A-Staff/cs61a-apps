import React from "react";
import "./Prompt.css";
import Character from "./Character.js";

export default function Prompt(props) {
  const { promptedWords } = props;
  const { typedWords } = props;
  const { currWord } = props;
  const words = [];
  let pastEnd = false;
  for (let i = 0; i !== promptedWords.length; ++i) {
    const promptedWord = promptedWords[i];
    const typedWord = typedWords[i];
    if (typedWord) {
      const correct = promptedWord === typedWord;
      for (const char of promptedWord) {
        words.push(
          <Character
            key={words.length}
            char={char}
            correct={correct}
            wrong={!correct}
          />
        );
      }
      words.push(<Character key={words.length} char=" " />);
    } else if (!pastEnd) {
      for (let j = 0; j !== promptedWord.length; ++j) {
        const correct = currWord[j] && promptedWord[j] === currWord[j];
        const wrong = currWord[j] && promptedWord[j] !== currWord[j];
        words.push(
          <Character
            key={words.length}
            char={promptedWord[j]}
            correct={correct}
            wrong={wrong}
          />
        );
      }
      words.push(<Character key={words.length} char=" " />);
      pastEnd = true;
    } else {
      for (const char of promptedWord) {
        words.push(<Character key={words.length} char={char} />);
      }
      words.push(<Character key={words.length} char=" " />);
    }
  }
  return (
    <div className="PromptBox">
      Look at the following words:
      <div className="Prompt">{words}</div>
    </div>
  );
}
