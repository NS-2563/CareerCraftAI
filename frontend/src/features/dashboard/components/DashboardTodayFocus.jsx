import { useNavigate } from "react-router-dom";
import { BookOpen, FileText, Mic, Sparkles } from "lucide-react";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { IconTile, InsightCard, SectionLabel, SignalStrengthBadge } from "@/components/ui/atoms";

const CATEGORY_CONFIG = {
  "New skill": { icon: BookOpen, accent: "var(--brand)" },
  "Resume wording": { icon: FileText, accent: "#3b82f6" },
  "Practice": { icon: Mic, accent: "#8b5cf6" },
};

const DEFAULT_CONFIG = { icon: Sparkles, accent: "var(--brand)" };

function categoryConfig(category) {
  return CATEGORY_CONFIG[category] ?? DEFAULT_CONFIG;
}

/**
 * "Today's Focus" — the single best signal-backed Career Coach recommendation
 * (Feature 12). Surfaces the top pick reusing Phase 2's real signal counts;
 * no fabricated time/effort estimate, ever.
 *
 * @param {{ focus: object|null }} props — `today_focus` from the dashboard summary:
 *   `{ skill, category, supported_signals, total_possible_signals, reasons[] }`.
 */
export function DashboardTodayFocus({ focus }) {
  const navigate = useNavigate();

  if (!focus || typeof focus !== "object") return null;

  const skill = focus.skill;
  const category = focus.category;
  const supported = Number(focus.supported_signals) || 0;
  const total = Number(focus.total_possible_signals) || 0;
  const reasons = Array.isArray(focus.reasons) ? focus.reasons : [];
  const { icon: Icon, accent } = categoryConfig(category);

  return (
    <section>
      <div className="mb-3 flex items-center justify-between gap-2">
        <SectionLabel>Today's Focus</SectionLabel>
        <Badge variant="soft" accent={accent}>
          {category}
        </Badge>
      </div>
      <InsightCard
        title={skill}
        icon={Icon}
        accent={accent}
        indicator={
          total > 0 ? (
            <SignalStrengthBadge supported={supported} total={total} accent={accent} />
          ) : undefined
        }
        reasons={reasons}
      />
      <Button
        variant="outline"
        size="sm"
        className="mt-3 gap-1.5"
        onClick={() => navigate("/career")}
      >
        <Sparkles className="size-4" /> Open in Career Coach
      </Button>
    </section>
  );
}

/**
 * Empty-state version: shown when there is no real, signal-backed
 * recommendation to surface (new user, no career report, or every
 * candidate has zero supported signals).
 */
export function DashboardTodayFocusEmpty() {
  const navigate = useNavigate();
  return (
    <section>
      <div className="mb-3 flex items-center justify-between gap-2">
        <SectionLabel>Today's Focus</SectionLabel>
      </div>
      <Card sheen className="flex items-center gap-3 p-5">
        <IconTile icon={Sparkles} accent="var(--brand)" size="sm" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">You're all caught up</p>
          <p className="text-xs text-muted-foreground">
            No new recommendations right now. Check back after your next resume
            analysis or career report.
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="shrink-0"
          onClick={() => navigate("/career")}
        >
          Run a career report
        </Button>
      </Card>
    </section>
  );
}

export default DashboardTodayFocus;
