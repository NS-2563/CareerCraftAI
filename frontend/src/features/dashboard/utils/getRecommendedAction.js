/**
 * Deterministic, AI-free prioritization of the single best next step for the user.
 * Rules are evaluated in strict priority order:
 *   1. No resume                → Resume Studio
 *   2. Resume, never analyzed   → Resume Analysis
 *   3. ATS score below 70       → Resume Analysis
 *   4. No applications          → Job Tracker
 *   5. No interview sessions    → Interview Prep
 *   6. Career readiness < 60    → Career Coach
 *   7. Otherwise                → "You're making excellent progress."
 */

const ACTIONS = {
  resume: {
    id: "resume",
    title: "Resume Studio",
    description: "Start by creating your first resume.",
    priorityLabel: "Create your first resume",
    path: "/resume-studio",
    ctaLabel: "Continue",
    priority: 1,
  },
  resume_analysis: {
    id: "resume_analysis",
    title: "Resume Analysis",
    description: "Analyze your resume to uncover improvement areas.",
    priorityLabel: "Analyze your resume",
    path: "/resume",
    ctaLabel: "Continue",
    priority: 2,
  },
  ats: {
    id: "ats",
    title: "Resume Analysis",
    description: "Improve your ATS score to increase interview chances.",
    priorityLabel: "Improve ATS score",
    path: "/resume",
    ctaLabel: "Continue",
    priority: 3,
  },
  jobs: {
    id: "jobs",
    title: "Job Tracker",
    description: "Track your first application to move your search forward.",
    priorityLabel: "Track your first application",
    path: "/jobs",
    ctaLabel: "Continue",
    priority: 4,
  },
  interview: {
    id: "interview",
    title: "Interview Prep",
    description: "Practice your first interview with AI-powered questions.",
    priorityLabel: "Practice your first interview",
    path: "/interview/dashboard",
    ctaLabel: "Continue",
    priority: 5,
  },
  career_coach: {
    id: "career_coach",
    title: "Career Coach",
    description: "Get a personalized strategy to lift your readiness score.",
    priorityLabel: "Raise your readiness score",
    path: "/career",
    ctaLabel: "Continue",
    priority: 6,
  },
  complete: {
    id: "complete",
    title: "You're making excellent progress",
    description: "Every step compounds — keep the momentum going.",
    priorityLabel: "Keep up the momentum",
    path: null,
    ctaLabel: null,
    priority: 7,
  },
};

/**
 * @param {{
 *   resumeCount?: number
 *   hasAnalysis?: boolean
 *   atsScore?: number|null
 *   applicationCount?: number
 *   interviewCount?: number
 *   readinessScore?: number|null
 * }} [inputs]
 * @returns {{
 *   id: string, title: string, description: string, priorityLabel: string,
 *   path: string|null, ctaLabel: string|null, priority: number
 * }}
 */
export function getRecommendedAction({
  resumeCount = 0,
  hasAnalysis = false,
  atsScore = null,
  applicationCount = 0,
  interviewCount = 0,
  readinessScore = null,
} = {}) {
  if (resumeCount === 0) return ACTIONS.resume;
  if (!hasAnalysis) return ACTIONS.resume_analysis;
  if (atsScore != null && atsScore < 70) return ACTIONS.ats;
  if (applicationCount === 0) return ACTIONS.jobs;
  if (interviewCount === 0) return ACTIONS.interview;
  if (readinessScore != null && readinessScore < 60) return ACTIONS.career_coach;
  return ACTIONS.complete;
}
