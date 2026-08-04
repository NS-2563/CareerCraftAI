import { ClipboardList, FileText, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { InsightCard } from "@/components/ui/atoms";

const INSIGHT_META = {
  jd_match_gaps: { icon: ClipboardList, accent: "#f59e0b" },
  resume_suggestions: { icon: FileText, accent: "#8b5cf6" },
};

/**
 * Dismissible insight cards rendered above the workspace tabs. Every card is a
 * deterministic derivation of data that already exists (JD match gaps, resume
 * analysis suggestions) — never an AI-judged quality score. Dismissals are
 * persisted per user+application so a dismissed card does not reappear.
 *
 * @param {{
 *   insights: Array<{ key: string, title: string, description: string, reasons: string[], extra_count?: number }>
 *   onDismiss?: (key: string) => void
 * }} props
 */
export default function WorkspaceInsights({ insights = [], onDismiss }) {
  if (!insights.length) return null;

  return (
    <div className="flex flex-col gap-3">
      {insights.map((insight) => {
        const meta = INSIGHT_META[insight.key] || { icon: ClipboardList, accent: "var(--brand)" };
        const Icon = meta.icon;
        const reasons = [
          ...(insight.reasons || []),
          ...(insight.extra_count > 0 ? [`and ${insight.extra_count} more`] : []),
        ];
        return (
          <InsightCard
            key={insight.key}
            title={insight.title}
            icon={Icon}
            accent={meta.accent}
            reasons={reasons}
            indicator={
              onDismiss ? (
                <Button
                  variant="ghost"
                  size="icon-xs"
                  onClick={() => onDismiss(insight.key)}
                  aria-label={`Dismiss ${insight.title}`}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X />
                </Button>
              ) : null
            }
          >
            <p className="text-xs text-muted-foreground">{insight.description}</p>
          </InsightCard>
        );
      })}
    </div>
  );
}
