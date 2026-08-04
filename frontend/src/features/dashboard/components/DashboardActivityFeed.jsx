import { Link, useNavigate } from "react-router-dom";
import { Clock, ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { IconTile, SectionLabel } from "@/components/ui/atoms";
import { accentFor, iconFor, moduleForEvent } from "@/features/dashboard/utils/moduleLookup";
import { formatTimeAgo, formatGroupDay } from "@/utils/dates";

/**
 * Group activity items by day, preserving chronological order.
 * @param {Array<{ created_at: string|null }>} activities
 */
function groupByDay(activities) {
  const groups = [];
  for (const act of activities) {
    const day = formatGroupDay(act.created_at);
    const last = groups[groups.length - 1];
    if (last && last.day === day) {
      last.items.push(act);
    } else {
      groups.push({ day, items: [act] });
    }
  }
  return groups;
}

/**
 * Recent activity feed grouped by day (Feature 6).
 * @param {{ activities: Array<object>, viewAllPath?: string }} props
 */
export function DashboardActivityFeed({ activities = [], viewAllPath = null }) {
  const groups = groupByDay(activities);

  return (
    <Card className="p-5" sheen>
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="size-4 text-muted-foreground" />
          <SectionLabel>Recent activity</SectionLabel>
        </div>
        {viewAllPath && (
          <Link to={viewAllPath} className="text-xs text-primary hover:underline">
            View all
          </Link>
        )}
      </div>

      {groups.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <p className="text-sm font-medium">No recent activity yet</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Resume edits, interviews, and applications will appear here.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-5">
          {groups.map((group) => (
            <div key={group.day}>
              <p className="mb-2 text-xs font-medium text-muted-foreground">{group.day}</p>
              <ul className="flex flex-col gap-3.5">
                {group.items.slice(0, 5).map((act) => {
                  const moduleId = moduleForEvent(act.event_type);
                  const accent = moduleId ? accentFor(moduleId) : "var(--brand)";
                  const Icon = moduleId ? iconFor(moduleId) : Clock;
                  return (
                    <li key={act.id} className="flex gap-3">
                      <IconTile icon={Icon} accent={accent} size="sm" />
                      <div className="min-w-0">
                        <p className="text-sm text-pretty">{act.title}</p>
                        {act.description && (
                          <p className="truncate text-xs text-muted-foreground">
                            {act.description}
                          </p>
                        )}
                        <p className="text-xs text-muted-foreground">
                          {formatTimeAgo(act.created_at)}
                        </p>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

/**
 * Empty-state activity feed (Feature 10).
 */
export function DashboardActivityEmpty({ onCreate }) {
  const navigate = useNavigate();
  return (
    <Card className="p-5" sheen>
      <div className="mb-4 flex items-center gap-2">
        <Clock className="size-4 text-muted-foreground" />
        <SectionLabel>Recent activity</SectionLabel>
      </div>
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <p className="text-sm font-medium">No recent activity yet</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Resume edits, interviews, and applications will appear here.
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

export default DashboardActivityFeed;
