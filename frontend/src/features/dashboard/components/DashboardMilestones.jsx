import { Trophy, Check, Circle } from "lucide-react";

import { Card } from "@/components/ui/card";
import { SectionLabel } from "@/components/ui/atoms";

/**
 * Career milestones — first-occurrence achievements derived strictly from the
 * real Activity Log (feature intro). Each row is a real, achieved/not-achieved
 * state backed by an actual logged activity event; nothing is fabricated.
 *
 * @param {{
 *   milestones: Array<{ key, label, description, achieved, achieved_at }>
 * }} props
 */
export function DashboardMilestones({ milestones = [] }) {
  if (!Array.isArray(milestones)) return null;

  const achieved = milestones.filter((m) => m.achieved === true).length;
  const accent = "var(--brand)";

  return (
    <Card className="p-5" sheen>
      <div className="mb-4 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Trophy className="size-4 text-muted-foreground" />
          <SectionLabel>Milestones</SectionLabel>
        </div>
        {milestones.length > 0 && (
          <span className="text-xs text-muted-foreground tabular-nums">
            {achieved}/{milestones.length} unlocked
          </span>
        )}
      </div>

      {milestones.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Your unlocked milestones will appear here as you use the app.
        </p>
      ) : (
        <ul className="flex flex-col">
          {milestones.map((milestone) => {
            const isAchieved = milestone.achieved === true;
            return (
              <li
                key={milestone.key}
                className="flex items-start gap-3 rounded-xl px-2 py-1.5"
              >
                {isAchieved ? (
                  <span
                    className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full"
                    style={{
                      color: "#fff",
                      backgroundColor: accent,
                    }}
                  >
                    <Check className="size-3" strokeWidth={3} />
                  </span>
                ) : (
                  <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full border border-muted-foreground/30 text-muted-foreground/40">
                    <Circle className="size-3" />
                  </span>
                )}
                <span className="min-w-0 flex-1">
                  <span
                    className={`block text-sm font-medium ${
                      isAchieved ? "" : "text-muted-foreground"
                    }`}
                  >
                    {milestone.label}
                  </span>
                  <span className="block text-xs text-muted-foreground">
                    {milestone.description}
                  </span>
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}

export default DashboardMilestones;