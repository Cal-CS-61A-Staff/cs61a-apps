import { PYTHON, SCHEME, SQL } from "../../common/languages.js";
import pyFormat from "../../languages/python/utils/format.js";
import scmFormat from "../../languages/scheme/utils/format.js";
import pyGenerateDebugTrace from "../../languages/python/utils/generateDebugTrace.js";
import scmGenerateDebugTrace from "../../languages/scheme/utils/generateDebugTrace.js";
import { runPyCode, runPyFile } from "../../languages/python/utils/run.js";
import { runScmCode, runScmFile } from "../../languages/scheme/utils/run.js";
import SchemeDebugger from "../../languages/scheme/components/SchemeDebugger.js";
import PythonTutorDebug from "../../languages/python/components/PythonTutorDebug.js";
import pyDebugPrefix from "../../languages/python/utils/debugPrefix.js";
import scmDebugPrefix from "../../languages/scheme/utils/debugPrefix.js";
import { runSQLCode } from "../../languages/sql/utils/run.js";
import ProcessPool from "./processPool.js";

export function format(language) {
  const options = {
    [PYTHON]: pyFormat,
    [SCHEME]: scmFormat,
  };
  return options[language];
}

export function generateDebugTrace(language) {
  const options = {
    [PYTHON]: pyGenerateDebugTrace,
    [SCHEME]: scmGenerateDebugTrace,
  };
  return options[language];
}

const interpreterPool = new ProcessPool(
  {
    [PYTHON]: runPyCode,
    [SCHEME]: runScmCode,
    [SQL]: runSQLCode,
  },
  2
);

export function runCode(language) {
  return interpreterPool.pop(language);
}

export function runFile(language) {
  const options = {
    [PYTHON]: runPyFile,
    [SCHEME]: runScmFile,
  };
  return options[language];
}

export function Debugger(language) {
  const options = {
    [PYTHON]: PythonTutorDebug,
    [SCHEME]: SchemeDebugger,
    [SQL]: SchemeDebugger, // temp!
  };
  return options[language];
}

export function debugPrefix(language) {
  const options = {
    [PYTHON]: pyDebugPrefix,
    [SCHEME]: scmDebugPrefix,
  };
  return options[language];
}

export function extension(language) {
  const extensions = {
    PYTHON: ".py",
    SCHEME: ".scm",
    SQL: ".sql",
  };
  return extensions[language];
}
