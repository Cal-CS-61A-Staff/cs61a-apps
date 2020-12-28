import { REGISTER_OKPY_HANDLER } from "../../common/communicationEnums.js";
import { send } from "./communication";

export default function registerOKPyHandler(onOKPypdate) {
  const [, , detach] = send({ type: REGISTER_OKPY_HANDLER }, (data) => {
    const { raw, modules, path } = data;
    onOKPypdate(parseRaw(raw), modules, path);
  });
  return detach;
}

function parseRaw(raw) {
  const CASE_DELIM = `${"-".repeat(69)}\n`;
  const tests = raw.split(CASE_DELIM);
  const out = [];
  for (const test of tests) {
    parseTest(test, out);
  }
  return out;
}

const PS1 = ">>> ";
const PS2 = "... ";
const COMMENT = "#";

function parseTest(test, out) {
  // heuristic to check if there's any code to run
  if (!test.includes(PS1)) {
    return;
  }
  const lines = test.split("\n");
  const testName = parseTestName(lines[0]);
  const testCode = parseTestCode(lines.slice(1));

  out.push({
    name: testName,
    rawName: lines[0],
    ...testCode,
    raw: test,
  });
}

function parseTestName(rawName) {
  if (rawName.includes(">")) {
    // fmt: problem > suite > case
    return rawName.split(" > ");
  } else {
    // fmt: doctest
    return [rawName.substr("Doctests for ".length)].concat(["Doctests"]);
  }
}

function parseTestCode(lines) {
  const code = [];
  let i;
  for (i = 0; i !== lines.length; ++i) {
    if (lines[i].startsWith(PS1) || lines[i].startsWith(PS2)) {
      code.push(lines[i].substr(PS1.length));
    }
    if (lines[i].includes("# Error")) {
      break;
    }
  }

  const success = i === lines.length;

  if (!success) {
    // failed test case
    for (; i !== lines.length; ++i) {
      if (lines[i].startsWith(COMMENT)) {
        code.push(lines[i]);
      } else {
        break;
      }
    }
  }

  return { success, code };
}
