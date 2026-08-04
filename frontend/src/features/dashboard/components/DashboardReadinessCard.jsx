import { useNavigate } from "react-router-dom";
import { Compass, ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SectionLabel, ProgressRing, ScoreTooltip } from "@/components/ui/atoms";
import { getReadinessStatus } from "@/features/dashboard/utils/getReadinessStatus";

/**
 * Career readiness score card with band label and ATS mini-stat (Feature 4).
 * @param {{
 *   readiness: object|null
 *   atsLatest: number|null
 * }} props
 */
export function DashboardReadinessCard({ readiness, atsLatest = null }) {
  const navigate = useNavigate();
  const status = getReadinessStatus(readiness?.score ?? null);
  const hasScore = status.value != null;

  return (
    <Card className="flex flex-col items-center justify-center gap-3 p-6 text-center" sheen>
      {hasScore ? (
        <>
          <SectionLabel>Career readiness</SectionLabel>
          <ScoreTooltip description="Weighted blend: 40% your ATS resume score, 30% skill match, 15% for having a Projects section, and 15% for Certifications.">
            <ProgressRing
              value={status.value}
              accent="var(--brand)"
              label={String(status.value)}
              sublabel="/ 100"
              size={128}
              stroke={11}
            />
          </ScoreTooltip>
          <p className="text-sm font-medium">{status.label}</p>
          <p className="text-xs text-muted-foreground">{status.description}</p>
          {atsLatest != null && (
            <p className="text-xs text-muted-foreground">
              Latest ATS score:{" "}
              <span className="font-medium text-foreground">{Math.round(atsLatest)}</span>/100
            </p>
          )}
        </>
      ) : (
        <>
          <div className="flex size-12 items-center justify-center rounded-2xl border text-[var(--amber)]"
            style={{
              backgroundColor: "color-mix(in oklch, var(--amber) 15%, transparent)",
              borderColor: "color-mix(in oklch, var(--amber) 26%, transparent)",
            }}
          >
            <Compass className="size-6" strokeWidth={2} />
          </div>
          <SectionLabel>Career readiness</SectionLabel>
          <p className="text-sm text-muted-foreground">
            Run AI Career Coach to get your readiness score.
          </p>
          <Button variant="outline" size="sm" onClick={() => navigate("/career")} className="gap-1.5">
            <Compass className="size-4" /> Talk to coach <ArrowUpRight className="size-3.5" />
          </Button>
        </>
      )}
    </Card>
  );
}

export default DashboardReadinessCard;
