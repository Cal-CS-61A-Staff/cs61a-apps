import { sendNoInteract } from "../../../renderer/utils/communication";
import { GEN_PY_TRACE } from "../constants/communicationEnums";
import { PYTHON } from "../../../common/languages.js";
import debugPrefix from "./debugPrefix.js";

const MAX_GLOBALS = 10;

export default async function generateDebugTrace(
  code,
  modules = {},
  setup_code = "",
  working_directory = ""
) {
  const params = {
    code,
    modules,
    setup_code,
    working_directory,
  };

  const data = JSON.parse(
    await sendNoInteract({
      handler: PYTHON,
      type: GEN_PY_TRACE,
      data: params,
    })
  );

  // filter debug code
  if (data.code.main_code.startsWith(debugPrefix)) {
    data.code.main_code = data.code.main_code.substr(debugPrefix.length);
    const numDebugLines = debugPrefix.split("\n").length;
    const newTrace = [];
    for (const point of data.trace) {
      if (point.line === undefined) {
        newTrace.push(point);
      } else if (point.line >= numDebugLines) {
        point.line -= numDebugLines - 1;
        newTrace.push(point);
      }
    }
    data.trace = newTrace;
  }

  // filter for excessive globals

  if (data.trace.length === 1 && data.trace[0].event === "uncaught_exception") {
    return { success: false, error: data.trace[0].exception_msg };
  }

  const globals =
    data.trace[Math.max(data.trace.length - 2, 0)].ordered_globals;

  if (globals.length < MAX_GLOBALS) {
    return { success: true, data };
  }

  const requiredGlobals = new Set();

  for (const point of data.trace) {
    for (const frame of point.stack_to_render) {
      requiredGlobals.add(frame.func_name);
      for (const local of frame.ordered_varnames) {
        requiredGlobals.add(local);
      }
    }
  }

  for (const point of data.trace) {
    const displayedGlobals = [];
    for (const global of point.ordered_globals) {
      if (requiredGlobals.has(global)) {
        displayedGlobals.push(global);
      }
    }
    point.ordered_globals = displayedGlobals;
  }

  data.filtered = true;

  return { success: true, data };
}
