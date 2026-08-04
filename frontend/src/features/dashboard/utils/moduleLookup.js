import { ChevronRight } from "lucide-react";
import { modules } from "@/lib/modules";

export const MODULE_BY_ID = Object.fromEntries(modules.map((m) => [m.id, m]));

export function accentFor(moduleId) {
  return MODULE_BY_ID[moduleId]?.accent ?? "var(--brand)";
}

export function iconFor(moduleId) {
  return MODULE_BY_ID[moduleId]?.icon ?? ChevronRight;
}

/**
 * Map an activity event_type to the module that produced it.
 * @param {string} [eventType]
 * @returns {string|null}
 */
export function moduleForEvent(eventType = "") {
  if (eventType.startsWith("resume")) return "resume-studio";
  if (eventType.startsWith("analysis")) return "resume-analysis";
  if (eventType.startsWith("cover_letter")) return "cover-letter";
  if (eventType.startsWith("career")) return "career-coach";
  if (eventType.startsWith("job_application") || eventType.startsWith("jd_match")) return "jobs";
  if (eventType.startsWith("interview")) return "interview-prep";
  if (eventType.startsWith("communication")) return "communication";
  return null;
}
