import { DOCTEST_MARKER } from "../../../renderer/components/File";
import { runScmCode } from "./run";

const STOP_MARKER = "STOP: ";

export default function test(code, onSuccess, onError) {
  const doctestData = [];
  const errors = [];
  const [, killCallback, detachCallback] = runScmCode(
    `(define __run_all_doctests 1)\n${code}\n(display "${STOP_MARKER}")`,
    (out) => {
      if (out.startsWith(DOCTEST_MARKER)) {
        const rawData = out.slice(DOCTEST_MARKER.length);
        // eslint-disable-next-line no-eval
        const caseData = (0, eval)(`(${rawData})`);
        doctestData.push(caseData);
      } else if (out.startsWith(STOP_MARKER)) {
        killCallback();
        detachCallback();
        if (errors.length === 0) {
          onSuccess(doctestData);
        } else {
          onError(errors.join("\n"));
        }
      }
    },
    (err) => {
      if (err.trim() !== "scm>") {
        // something went wrong in setup
        errors.push(err.trim());
      }
    },
    () => {}
  );

  return () => {
    detachCallback();
    killCallback();
  };
}
