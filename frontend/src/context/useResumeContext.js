import { useContext } from "react";
import { ResumeContext } from "./ResumeContext.store";

export function useResumeContext() {
  const ctx = useContext(ResumeContext);
  if (!ctx) throw new Error("useResumeContext must be used within a ResumeProvider");
  return ctx;
}
