import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { IconTile } from "@/components/ui/atoms";
import { accentFor, iconFor } from "@/features/dashboard/utils/moduleLookup";
import { formatTimeAgo } from "@/utils/dates";

function StatCard({ moduleId, label, value, context, delta, sublines, to }) {
  const Icon = iconFor(moduleId);
  const accent = accentFor(moduleId);

  return (
    <Link
      to={to}
      className="group block h-full rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-ring/60"
      aria-label={`${label}: ${value ?? "no data"}`}
    >
      <Card className="h-full p-5 transition-all duration-300 group-hover:-translate-y-0.5 group-hover:border-[color-mix(in_oklch,var(--foreground)_18%,transparent)]" sheen>
        <div className="flex items-start justify-between">
          <IconTile icon={Icon} accent={accent} />
          <ArrowUpRight className="size-4 text-muted-foreground transition-all group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-foreground" />
        </div>
        <p className="mt-4 font-display text-2xl font-semibold tabular-nums">{value ?? "—"}</p>
        <p className="text-sm text-muted-foreground">{label}</p>
        {delta != null && delta > 0 && (
          <Badge variant="soft" accent="var(--emerald)" className="mt-2">
            +{delta} this week
          </Badge>
        )}
        {context && (
          <p className="mt-1 text-xs" style={{ color: accent }}>
            {context}
          </p>
        )}
        {sublines?.length > 0 && (
          <p className="mt-1 text-xs text-muted-foreground">{sublines.join(" · ")}</p>
        )}
      </Card>
    </Link>
  );
}

/**
 * Enhanced statistics cards (Feature 5).
 * @param {{
 *   resume: object|null
 *   jobStats: object|null
 *   interview: object|null
 *   careerReadiness: object|null
 *   jobPipeline: Array<{ status: string, count: number }>
 * }} props
 */
export function DashboardStatsGrid({ resume, jobStats, interview, careerReadiness, jobPipeline = [] }) {
  const resumeCount = resume?.count ?? 0;
  const applicationCount = jobStats?.total_applications ?? 0;
  const interviewCount = interview?.total_sessions ?? 0;
  const readinessScore = careerReadiness?.score ?? null;

  const offerCount = jobPipeline.find((p) => p.status === "Offer")?.count ?? 0;
  const interviewStageCount = jobStats?.interview_count ?? 0;

  const stats = [
    {
      moduleId: "resume-studio",
      label: "Resumes",
      value: resumeCount,
      to: "/resume-studio",
      context: resumeCount > 0 ? `Last edited ${formatTimeAgo(resume?.last_edited)}` : "Create your first resume to get started",
      delta: resume?.created_this_week ?? 0,
    },
    {
      moduleId: "jobs",
      label: "Applications",
      value: applicationCount,
      to: "/jobs",
      context:
        applicationCount > 0
          ? "Tracked in your job board"
          : "Start tracking your job applications",
      sublines:
        interviewStageCount > 0 || offerCount > 0
          ? [
              ...(interviewStageCount > 0 ? [`${interviewStageCount} interview${interviewStageCount === 1 ? "" : "s"}`] : []),
              ...(offerCount > 0 ? [`${offerCount} offer${offerCount === 1 ? "" : "s"}`] : []),
            ]
          : [],
    },
    {
      moduleId: "interview-prep",
      label: "Practice sessions",
      value: interviewCount,
      to: "/interview/dashboard",
      context:
        interview?.average_score != null
          ? `Average score: ${Math.round(interview.average_score)}%`
          : interviewCount > 0
            ? "Complete a session to see your score"
            : "Practice with AI-powered questions",
    },
    {
      moduleId: "career-coach",
      label: "Career readiness",
      value: readinessScore != null ? Math.round(readinessScore) : null,
      to: "/career",
      context:
        readinessScore != null
          ? `Last updated ${formatTimeAgo(careerReadiness?.last_updated)}`
          : "Run AI Career Coach to assess your readiness",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {stats.map((s) => (
        <StatCard key={s.moduleId} {...s} />
      ))}
    </div>
  );
}

export default DashboardStatsGrid;
