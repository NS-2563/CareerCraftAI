import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import careerApi from "@/services/careerApi";

function SkillGapInsightsContent({ data }) {
  const { has_data: hasData, insufficient_data: insufficient, message, total_applications: total, top_missing_skills: skills } = data;

  if (!hasData || insufficient) {
    return (
      <div className="rounded-lg border border-dashed p-5">
        <p className="text-sm text-muted-foreground">
          {message || "Not enough JD match data yet to compute a skill gap insight."}
        </p>
        <Link
          to="/jobs"
          className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
        >
          Run a resume match on a saved job
          <ArrowUpRight className="size-3.5" />
        </Link>
      </div>
    );
  }

  if (!skills || skills.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-5">
        <p className="text-sm text-muted-foreground">
          No missing skills recorded across your {total} saved job matches. Nice work — keep it up.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        Computed from your last{" "}
        <span className="font-medium text-foreground">{total}</span>{" "}
        saved job description matches.
      </p>

      <ul className="space-y-2">
        {skills.map((skill) => (
          <li
            key={skill.name}
            className="flex items-center justify-between gap-4 rounded-lg border bg-card px-4 py-3"
          >
            <span className="font-medium">{skill.name}</span>
            <span className="text-sm text-muted-foreground">
              required in {skill.count} of your last {total} applications
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function SkillGapInsights() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["skill-gap-summary"],
    queryFn: () => careerApi.getSkillGapSummary(),
    staleTime: 60_000,
  });

  return (
    <section className="rounded-xl border bg-card p-6">
      <h2 className="text-2xl font-bold mb-1">
        Skills Missing From Your Resume
      </h2>
      <p className="text-sm text-muted-foreground mb-6">
        Based on the skills required by jobs you&apos;ve already applied to — from your
        own application history.
      </p>

      {isLoading && (
        <div className="animate-pulse space-y-3">
          <div className="h-4 w-1/3 rounded bg-muted" />
          <div className="h-12 rounded-lg bg-muted" />
          <div className="h-12 rounded-lg bg-muted" />
        </div>
      )}

      {!isLoading && isError && (
        <div className="rounded-lg border border-dashed p-5">
          <p className="text-sm text-muted-foreground">
            Couldn&apos;t load your skill gap insight right now.
          </p>
        </div>
      )}

      {!isLoading && !isError && data && (
        <SkillGapInsightsContent data={data.data} />
      )}
    </section>
  );
}
