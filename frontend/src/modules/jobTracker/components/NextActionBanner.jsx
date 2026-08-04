import {
  ArrowRight,
  BookmarkPlus,
  ClipboardList,
  FileText,
  Link2,
  MessagesSquare,
  MessageSquarePlus,
  Send,
  Sparkles,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const NEXT_ACTION_META = {
  save_job_description: { icon: FileText, accent: "#0ea5e9" },
  link_resume: { icon: Link2, accent: "#8b5cf6" },
  run_jd_match: { icon: ClipboardList, accent: "#f59e0b" },
  generate_cover_letter: { icon: Send, accent: "#10b981" },
  send_follow_up: { icon: MessagesSquare, accent: "#3b82f6" },
  practice_interview: { icon: MessageSquarePlus, accent: "#ec4899" },
};

/**
 * Deterministic "next recommended action" banner shown at the top of an
 * application workspace. The recommendation comes from a fixed backend
 * decision tree over real completion state — never an AI value — and the CTA
 * simply switches to the workspace tab where the action can be completed.
 *
 * @param {{
 *   action: object|null
 *   onNavigate?: (tab: string) => void
 * }} props
 */
export default function NextActionBanner({ action, onNavigate }) {
  if (!action) return null;

  const meta = NEXT_ACTION_META[action.key] || { icon: Sparkles, accent: "var(--brand)" };
  const Icon = meta.icon;

  return (
    <Card className="gap-0 overflow-hidden border-l-4" style={{ borderLeftColor: meta.accent }}>
      <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <div className="flex items-start gap-3">
          <span
            className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg border"
            style={{
              color: meta.accent,
              backgroundColor: `color-mix(in oklch, ${meta.accent} 14%, transparent)`,
              borderColor: `color-mix(in oklch, ${meta.accent} 26%, transparent)`,
            }}
          >
            <Icon className="size-4" strokeWidth={2} />
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="text-sm font-semibold">{action.title}</p>
              <span
                className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[0.65rem] font-medium"
                style={{
                  color: meta.accent,
                  backgroundColor: `color-mix(in oklch, ${meta.accent} 12%, transparent)`,
                }}
              >
                <BookmarkPlus className="size-3" />
                Recommended next step
              </span>
            </div>
            <p className="mt-0.5 text-sm text-muted-foreground">{action.description}</p>
          </div>
        </div>
        <Button
          type="button"
          size="sm"
          className="shrink-0 gap-1.5"
          onClick={() => onNavigate?.(action.tab)}
        >
          {action.cta}
          <ArrowRight className="size-3.5" />
        </Button>
      </CardContent>
    </Card>
  );
}
