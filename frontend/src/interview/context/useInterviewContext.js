import { useContext } from "react";
import { InterviewContext } from "./InterviewContext";

export function useInterviewContext() {
  const ctx = useContext(InterviewContext);

  if (!ctx) {
    throw new Error(
      "useInterviewContext must be used within an InterviewProvider"
    );
  }

  return ctx;
}
