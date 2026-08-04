import { useNavigate } from "react-router-dom";
import { CalendarClock, ArrowUpRight, ChevronRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SectionLabel } from "@/components/ui/atoms";
import { formatRelativeDay } from "@/utils/dates";

const TONE_ACCENT = {
  good: "var(--emerald)",
  warn: "var(--amber)",
  danger: "var(--rose)",
};

/**
 * Upcoming tasks list, shown newest-deadline-first up to `max` (Feature 7).
 * @param {{
 *   tasks: Array<{ type: string, label: string, detail: string, date: string, path: string, tone: string }>
 *   max?: number
 * }} props
 */
export function DashboardUpcomingTasks({ tasks = [], max = 5 }) {
  const navigate = useNavigate();
  const visible = tasks.slice(0, max);

  return (
    <Card className="p-5" sheen>
      <div className="mb-4 flex items-center gap-2">
        <CalendarClock className="size-4 text-muted-foreground" />
        <SectionLabel>Upcoming tasks</SectionLabel>
      </div>
      {visible.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <p className="text-sm font-medium">All caught up</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Interview sessions, deadlines, and follow-ups will appear here.
          </p>
        </div>
      ) : (
        <ul className="flex flex-col gap-1">
          {visible.map((task, index) => {
            const accent = TONE_ACCENT[task.tone] ?? "var(--brand)";
            return (
              <li key={`${task.type}-${index}`}>
                <button
                  type="button"
                  onClick={() => task.path && navigate(task.path)}
                  disabled={!task.path}
                  className="group flex w-full items-start gap-3 rounded-xl px-2 py-2.5 text-left transition-colors hover:bg-muted/50 disabled:cursor-default"
                >
                  <span
                    className="mt-1 flex size-2 shrink-0 rounded-full"
                    style={{ backgroundColor: accent }}
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-medium text-pretty">{task.label}</span>
                    {task.detail && (
                      <span className="block truncate text-xs text-muted-foreground">
                        {task.detail}
                      </span>
                    )}
                  </span>
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <span style={{ color: accent }}>{formatRelativeDay(task.date)}</span>
                    {task.path && (
                      <ChevronRight className="size-3.5 opacity-0 transition-opacity group-hover:opacity-100" />
                    )}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}

/**
 * Empty-state upcoming tasks (Feature 10).
 */
export function DashboardUpcomingEmpty({ onCreate }) {
  const navigate = useNavigate();
  return (
    <Card className="p-5" sheen>
      <div className="mb-4 flex items-center gap-2">
        <CalendarClock className="size-4 text-muted-foreground" />
        <SectionLabel>Upcoming tasks</SectionLabel>
      </div>
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <p className="text-sm font-medium">All caught up</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Interview sessions, deadlines, and follow-ups will appear here.
        </p>
        {onCreate?.path && (
          <Button
            size="sm"
            variant="outline"
            className="mt-4 gap-1.5"
            onClick={() => navigate(onCreate.path)}
          >
            {onCreate.label} <ArrowUpRight className="size-3.5" />
          </Button>
        )}
      </div>
    </Card>
  );
}

export default DashboardUpcomingTasks;
