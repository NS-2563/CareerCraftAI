/**
 * Career readiness bands and the status label for a given 0–100 score.
 *
 *   0–39  → Needs Improvement
 *   40–69 → Developing
 *   70–84 → Strong
 *   85–100→ Excellent
 */

export const READINESS_BANDS = [
  {
    max: 39,
    label: "Needs Improvement",
    description: "Focus on the fundamentals to raise your score.",
    tone: "danger",
  },
  {
    max: 69,
    label: "Developing",
    description: "Consistent effort will move you forward.",
    tone: "warn",
  },
  {
    max: 84,
    label: "Strong",
    description: "You're in a great position. Keep refining.",
    tone: "good",
  },
  {
    max: 100,
    label: "Excellent",
    description: "You're fully prepared for the next step.",
    tone: "excellent",
  },
];

const NOT_ASSESSED = {
  label: "Not assessed",
  description: "Run AI Career Coach to assess your readiness.",
  tone: "muted",
  value: null,
  band: null,
};

/**
 * @param {number|null|undefined} score
 * @returns {{ label: string, description: string, tone: string, value: number|null, band: object|null }}
 */
export function getReadinessStatus(score) {
  if (score == null || Number.isNaN(Number(score))) {
    return NOT_ASSESSED;
  }
  const value = Math.round(Number(score));
  for (const band of READINESS_BANDS) {
    if (value <= band.max) {
      return { ...band, value, band };
    }
  }
  return {
    label: "Excellent",
    description: "You're fully prepared for the next step.",
    tone: "excellent",
    value,
    band: READINESS_BANDS[READINESS_BANDS.length - 1],
  };
}
