import { useEffect } from "react";

export default function useStyleWatcher(ref, callback, deps) {
  useEffect(() => {
    if (!ref.current) {
      return () => null;
    }
    const observer = new MutationObserver(callback);
    observer.observe(ref.current, {
      attributes: true,
      attributeFilter: ["style"],
    });
    return () => observer.disconnect();
  }, [ref.current, ...deps]);
}
