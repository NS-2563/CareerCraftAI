import { useNavigate } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { IconTile, SectionLabel } from "@/components/ui/atoms";
import { accentFor, iconFor, MODULE_BY_ID } from "@/features/dashboard/utils/moduleLookup";

const CONTINUE_MODULE = {
  resume: "resume-studio",
  cover_letter: "cover-letter",
  communication: "communication",
  interview: "interview-prep",
  job_application: "jobs",
};

/**
 * "Continue Where You Left Off" cards (Feature 3).
 * @param {{ items: object|null }} props — `continue_items` keyed by type.
 */
export function DashboardFocusCard({ items }) {
  const navigate = useNavigate();
  const entries = Object.entries(items || {});

  if (entries.length === 0) return null;

  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <SectionLabel>Continue where you left off</SectionLabel>
        <span className="text-xs text-muted-foreground">
          {entries.length} open {entries.length === 1 ? "item" : "items"}
        </span>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {entries.slice(0, 4).map(([key, item]) => {
          const moduleId = CONTINUE_MODULE[key] || "resume-studio";
          const Icon = iconFor(moduleId);
          const accent = accentFor(moduleId);
          const moduleName = MODULE_BY_ID[moduleId]?.name ?? "Open";
          return (
            <Card
              key={key}
              sheen
              className="h-full cursor-pointer p-5 transition-all duration-300 hover:-translate-y-0.5 hover:border-[color-mix(in_oklch,var(--foreground)_18%,transparent)] active:scale-[0.98]"
              onClick={() => navigate(item.path)}
            >
              <div className="flex items-start gap-4">
                <IconTile icon={Icon} accent={accent} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="truncate font-display font-semibold tracking-tight">
                      {item.label}
                    </h3>
                    <ArrowUpRight className="size-4 shrink-0 text-muted-foreground transition-all group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-foreground" />
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">{moduleName}</p>
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </section>
  );
}

/**
 * Empty-state version with a single CTA (Feature 10).
 */
export function DashboardFocusEmpty({ onCreate }) {
  const navigate = useNavigate();
  return (
    <section>
      <SectionLabel>Continue where you left off</SectionLabel>
      <Card className="mt-3 flex flex-col items-center gap-3 p-6 text-center" sheen>
        <p className="text-sm font-medium">Nothing in progress yet</p>
        <p className="text-xs text-muted-foreground">
          Start with a resume, a cover letter, or your first application.
        </p>
        <Button
          size="sm"
          onClick={() => navigate(onCreate?.path ?? "/resume-studio")}
          className="gap-1.5"
        >
          {onCreate?.label ?? "Create your first resume"}
        </Button>
      </Card>
    </section>
  );
}

export default DashboardFocusCard;
