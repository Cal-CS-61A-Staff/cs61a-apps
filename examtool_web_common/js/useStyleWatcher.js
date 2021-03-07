import { useEffect, useRef } from "react";

export default function useStyleWatcher(callback, deps) {
  const ref = useRef();

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

  return ref;
}
