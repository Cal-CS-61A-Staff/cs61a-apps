import { useEffect, useState } from "react";
import { addAuthListener, getCurrAuthData } from "./auth.js";

export function isStaff(authData) {
  return authData.data.participations.some(
    ({ course, role }) =>
      ["staff", "instructor", "grader"].includes(role) &&
      course.offering.startsWith("cal/cs61a/")
  );
}

export function useAuthData() {
  const [authData, setAuthData] = useState(getCurrAuthData());
  useEffect(() => addAuthListener(setAuthData), []);
  return authData;
}
