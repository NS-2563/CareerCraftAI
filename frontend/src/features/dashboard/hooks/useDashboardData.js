import { useQuery } from "@tanstack/react-query";
import dashboardApi from "@/services/dashboardApi";
import analyticsApi from "@/services/analyticsApi";
import { getJobs } from "@/modules/jobTracker/api/jobTrackerApi";
import { listSessions } from "@/modules/interview/services/interviewSessionApi";
import { getSuggestions } from "@/communication/services/communicationApi";
import { getRecommendedAction } from "@/features/dashboard/utils/getRecommendedAction";
import { daysUntil } from "@/utils/dates";

async function safe(fn) {
  try {
    return await fn();
  } catch {
    return null;
  }
}

function normalizeSuggestionType(type) {
  const t = (type || "").toLowerCase();
  if (t.includes("follow")) return "follow_up";
  if (t.includes("template")) return "template";
  if (t.includes("reminder")) return "reminder";
  return null;
}

const SUGGESTION_LABELS = {
  follow_up: "Send follow-up",
  template: "Review message template",
  reminder: "Send reminder",
};

/**
 * Build the sorted (soonest-first) upcoming tasks list (Feature 7).
 */
function buildUpcomingTasks({ jobs = [], sessions = null, suggestions = [] }) {
  const tasks = [];

  for (const job of jobs || []) {
    if (!job.deadline) continue;
    if (daysUntil(job.deadline) < 0) continue;
    const diff = daysUntil(job.deadline) ?? 0;
    tasks.push({
      type: "deadline",
      label: `Apply to ${job.job_title || "position"}`,
      detail: job.company || "",
      date: job.deadline,
      path: "/jobs",
      tone: diff === 0 ? "danger" : diff <= 3 ? "warn" : "good",
    });
  }

  const sessionItems = sessions?.data?.items || sessions?.items || [];
  for (const session of sessionItems) {
    if (session.completed_at) continue;
    tasks.push({
      type: "interview",
      label: "Resume interview practice",
      detail: session.job_title || `${session.question_count ?? 5} questions`,
      date: session.started_at || session.created_at,
      path: "/interview/practice",
      tone: "good",
    });
  }

  for (const suggestion of suggestions || []) {
    if (suggestion.is_dismissed || suggestion.is_actioned) continue;
    const kind = normalizeSuggestionType(suggestion.suggestion_type);
    if (!kind) continue;
    tasks.push({
      type: "suggestion",
      label: SUGGESTION_LABELS[kind],
      detail: [suggestion.job_company, suggestion.job_title].filter(Boolean).join(" — "),
      date: suggestion.created_at,
      path: "/communication",
      tone: "warn",
    });
  }

  return tasks
    .filter((t) => t.date)
    .sort((a, b) => new Date(a.date) - new Date(b.date))
    .slice(0, 5);
}

/**
 * Fan out across all dashboard data sources (Feature 8).
 * Every call is isolated so one module failure never breaks the page.
 *
 * Summary is the single source of truth for resume/job/interview/readiness
 * counts; the extra calls only fetch data the summary does not expose
 * (job deadlines, in-progress interview sessions, follow-up suggestions,
 * latest ATS snapshot) — no duplicate fetches.
 */
export function useDashboardData() {
  return useQuery({
    queryKey: ["dashboard-data"],
    staleTime: 60_000,
    retry: 1,
    queryFn: async () => {
      const [summary, jobs, sessions, suggestions, ats, healthScore, milestones] = await Promise.all([
        safe(() => dashboardApi.getSummary().then((res) => res.data?.data ?? null)),
        safe(() => getJobs()),
        safe(() => listSessions({ page: 1, pageSize: 50 })),
        safe(() => getSuggestions()),
        safe(() => analyticsApi.getHistory("ats_score", 1, true).then((res) => res.data?.data ?? null)),
        safe(() => dashboardApi.getHealthScore().then((res) => res.data?.data ?? null)),
        safe(() => dashboardApi.getMilestones().then((res) => res.data?.data?.milestones ?? null)),
      ]);
      return { summary, jobs, sessions, suggestions, ats, healthScore, milestones };
    },
    select: (data) => {
      const summary = data.summary ?? {};
      const resume = summary.resume ?? null;
      const jobStats = summary.job_stats ?? null;
      const interview = summary.interview ?? null;
      const careerReadiness = summary.career_readiness ?? null;
      const recentActivity = summary.recent_activity ?? [];
      const continueItems = summary.continue_items ?? {};
      const todayFocus = summary.today_focus ?? null;
      const careerJourney = summary.career_journey ?? [];
      const aiInsights = summary.ai_insights ?? [];
      const jobPipeline = summary.job_pipeline ?? [];
      const is_empty = summary.is_empty ?? false;

      const resumeCount = resume?.count ?? 0;
      const applicationCount = jobStats?.total_applications ?? 0;
      const interviewCount = interview?.total_sessions ?? 0;
      const readinessScore = careerReadiness?.score ?? null;

      const journeyMap = Object.fromEntries(
        (careerJourney || []).map((s) => [s.id, s.status])
      );
      const atsLatest = data.ats?.items?.[0]?.value ?? null;

      const recommendedAction = getRecommendedAction({
        resumeCount,
        hasAnalysis: journeyMap.analysis === "complete",
        atsScore: atsLatest,
        applicationCount,
        interviewCount,
        readinessScore,
      });

      const upcomingTasks = buildUpcomingTasks({
        jobs: data.jobs,
        sessions: data.sessions,
        suggestions: data.suggestions,
      });

      return {
        is_empty,
        resume,
        jobStats,
        interview,
        careerReadiness,
        recentActivity,
        continueItems,
        todayFocus,
        careerJourney,
        aiInsights,
        jobPipeline,
        pendingFollowUps: summary.pending_follow_ups ?? 0,
        atsLatest,
        recommendedAction,
        upcomingTasks,
        healthScore: data.healthScore,
        milestones: data.milestones ?? [],
      };
    },
  });
}
