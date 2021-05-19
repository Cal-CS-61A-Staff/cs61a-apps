import { PS1, PS2 } from "../constants/prompts";

const DOCTEST_START = "%doctest";
const DOCTEST_END = "%end";

export default function extractLarkTests(text) {
  const lines = text.split("\n");
  const grammar = [];
  const cases = [];

  let inDoctest = false;
  let caseName = null;
  let currentCase = null;
  let currentInput = [];
  let currentOutput = [];

  for (let lineNum = 0; lineNum !== lines.length; ++lineNum) {
    const line = lines[lineNum];
    const trimmedLine = line.trimEnd();
    if (inDoctest) {
      if (trimmedLine === DOCTEST_END || trimmedLine.startsWith(PS1)) {
        if (currentInput.length !== 0) {
          currentCase.push({
            input: currentInput.join("\n"),
            output: currentOutput.join("\n"),
          });
          currentInput = [];
          currentOutput = [];
        }
        if (trimmedLine === DOCTEST_END) {
          cases.push({ caseName, tests: currentCase });
          currentCase = null;
          inDoctest = false;
        } else {
          currentInput.push(line.slice(PS1.length));
        }
      } else if (trimmedLine.startsWith(PS2)) {
        if (currentInput.length === 0 || currentOutput.length !== 0) {
          throw Error(`Unexpected prompt ${PS2.trim()} on line ${lineNum}`);
        }
        currentInput.push(line.slice(PS2.length));
      } else {
        if (currentInput.length === 0) {
          throw Error(
            `${PS1.trim()} input must be provided before the expected output on line ${lineNum}.`
          );
        }
        currentOutput.push(trimmedLine);
      }
    } else if (trimmedLine.startsWith(DOCTEST_START)) {
      inDoctest = true;
      caseName = trimmedLine.slice(DOCTEST_START.length).trim();
      currentCase = [];
    } else {
      grammar.push(trimmedLine);
    }
  }

  if (inDoctest) {
    throw Error(`${DOCTEST_START} block not terminated with ${DOCTEST_END}`);
  }

  return { grammar: grammar.join("\n"), cases };
}
