import { Activity, Info } from "lucide-react";

import { Card } from "@/components/ui/card";
import { SectionLabel, ProgressRing, ScoreTooltip } from "@/components/ui/atoms";

const ACCENTS = {
  ats: "var(--brand)",
  interview: "#8b5cf6",
  jd_match: "#0ea5e9",
};

/**
 * Career Health Score card — a disclosed, weighted mean of real sub-metrics
 * (ATS score 40%, interview average 30%, JD-match coverage 30%). Every number
 * shown is stored data or the documented formula over it; when fewer than two
 * real sub-metrics exist the card says "not enough data yet" instead of
 * inventing a score.
 *
 * @param {{
 *   healthScore: {
 *     available: boolean
 *     score: number|null
 *     reason: string|null
 *     minimum_sub_metric_reason: string|null
 *     sub_metrics: Array<{ key, label, available, value, weight, effective_weight }>
 *   }|null
 * }} props
 */
export function DashboardHealthScore({ healthScore }) {
  if (!healthScore || typeof healthScore !== "object") return null;

  const available = healthScore.available === true;
  const score = healthScore.score;
  const subMetrics = Array.isArray(healthScore.sub_metrics) ? healthScore.sub_metrics : [];
  const present = subMetrics.filter((m) => m.available === true);

  return (
    <Card className="flex flex-col items-center gap-4 p-6 text-center" sheen>
      <div className="flex items-center gap-2">
        <Activity className="size-4 text-muted-foreground" />
        <SectionLabel>Career health</SectionLabel>
      </div>

      {available ? (
        <>
          <ScoreTooltip description="Weighted mean of your real sub-metrics: ATS/resume score (40%), interview average (30%), JD-match coverage (30%). Each is shown below; a sub-metric counts only when you have real data for it.">
            <ProgressRing
              value={Math.round(score ?? 0)}
              accent="var(--brand)"
              label={String(Math.round(score ?? 0))}
              sublabel="/ 100"
              size={128}
              stroke={11}
            />
          </ScoreTooltip>
          <ul className="flex w-full flex-col gap-1.5">
            {subMetrics.map((metric) => {
              const accent = ACCENTS[metric.key] ?? "var(--brand)";
              const presentValue = metric.available === true && metric.value != null;
              return (
                <li key={metric.key} className="flex items-center justify-between gap-2 text-xs">
                  <span className="flex min-w-0 items-center gap-1.5 truncate text-muted-foreground">
                    <span
                      aria-hidden
                      className="size-2 shrink-0 rounded-full"
                      style={{ backgroundColor: presentValue ? accent : "color-mix(in oklch, var(--foreground) 20%, transparent)" }}
                    />
                    <span className="truncate">{metric.label}</span>
                  </span>
                  <span className="shrink-0 font-medium tabular-nums text-foreground">
                    {presentValue ? `${Math.round(metric.value)}/100` : "—"}
                  </span>
                </li>
              );
            })}
          </ul>
        </>
      ) : (
        <div className="flex flex-col items-center gap-3 py-2">
          <div
            className="flex size-12 items-center justify-center rounded-2xl border text-muted-foreground"
            style={{
              backgroundColor: "color-mix(in oklch, var(--foreground) 6%, transparent)",
              borderColor: "color-mix(in oklch, var(--foreground) 14%, transparent)",
            }}
          >
            <Activity className="size-6" strokeWidth={2} />
          </div>
          <p className="text-sm font-medium">Not enough data yet</p>
          <p className="text-xs text-muted-foreground">
            {healthScore.minimum_sub_metric_reason ||
              "Complete a resume analysis, interviews, and job matches to unlock your Career Health Score."}
          </p>
        </div>
      )}

      <p className="flex items-start gap-1 text-[0.7rem] leading-relaxed text-muted-foreground/70">
        <Info className="mt-0.5 size-3 shrink-0" aria-hidden />
        {available ? (
          <span>
            Weighted from your {present.length} real sub-metric{present.length === 1 ? "" : "s"}.
            Hover the ring for the full formula.
          </span>
        ) : (
          <span>At least 2 real sub-metrics are required before a score is shown.</span>
        )}
      </p>
    </Card>
  );
}

export default DashboardHealthScore;
