import { DOCTEST_MARKER } from "../../../renderer/components/File";
import { runPyCode } from "./run";

export default function test(code, onSuccess, onError) {
  let commandSent = false;
  const [interactCallback, killCallback, detachCallback] = runPyCode(
    code,
    (out) => {
      if (!out.startsWith(DOCTEST_MARKER)) {
        return;
      }
      const rawData = out.slice(DOCTEST_MARKER.length);
      // eslint-disable-next-line no-eval
      const doctestData = (0, eval)(rawData);
      killCallback();
      onSuccess(doctestData);
    },
    (err) => {
      if (err.trim() !== ">>>") {
        // something went wrong in setup
        killCallback();
        detachCallback();
        onError(err.trim());
        commandSent = true;
      }
      if (!commandSent) {
        commandSent = true;
        interactCallback("__run_all_doctests()\n");
      }
    },
    () => {}
  );

  return () => {
    detachCallback();
    killCallback();
  };
}
