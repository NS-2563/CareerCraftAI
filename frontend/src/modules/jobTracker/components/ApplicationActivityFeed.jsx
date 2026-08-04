import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { History } from "lucide-react";

import { Card } from "@/components/ui/card";
import { Skeleton, Timeline } from "@/components/ui/atoms";
import { SectionLabel } from "@/components/ui/atoms";
import { accentFor, iconFor, moduleForEvent } from "@/features/dashboard/utils/moduleLookup";
import { formatTimeAgo } from "@/utils/dates";
import activityApi from "@/services/activityApi";

/**
 * Per-application Recent Activity feed rendered inside the workspace. Shows the
 * real cross-module activity events logged against this application (resume,
 * cover letter, JD match, communication, interview) via the existing activity
 * endpoint filtered by ``job_application_id``.
 *
 * @param {{
 *   jobApplicationId: number|string|null
 *   limit?: number
 * }} props
 */
export default function ApplicationActivityFeed({ jobApplicationId, limit = 20 }) {
  const query = useQuery({
    queryKey: ["applicationActivity", jobApplicationId],
    queryFn: () =>
      activityApi
        .getFeed({ jobApplicationId, limit })
        .then((res) => res.data?.data?.items ?? []),
    enabled: jobApplicationId !== undefined && jobApplicationId !== null,
    retry: false,
  });

  const timelineItems = useMemo(
    () =>
      (query.data || []).map((e) => {
        const moduleId = moduleForEvent(e.event_type);
        const accent = moduleId ? accentFor(moduleId) : "var(--brand)";
        return {
          id: e.id,
          title: e.title,
          subtitle: e.description || undefined,
          timestamp: formatTimeAgo(e.created_at),
          accentColor: accent,
        };
      }),
    [query.data]
  );

  return (
    <Card className="p-5" sheen>
      <div className="mb-4 flex items-center gap-2">
        <History className="size-4 text-muted-foreground" />
        <SectionLabel>Recent activity</SectionLabel>
      </div>

      {query.isPending ? (
        <div className="space-y-3">
          <Skeleton className="h-12 rounded-lg" />
          <Skeleton className="h-12 rounded-lg" />
        </div>
      ) : timelineItems.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No activity recorded for this application yet. Actions like running Resume
          Match, saving a cover letter, or logging outreach will appear here.
        </p>
      ) : (
        <Timeline
          items={timelineItems}
          iconFor={(item) => {
            const ev = (query.data || []).find((e) => e.id === item.id);
            const moduleId = ev ? moduleForEvent(ev.event_type) : null;
            return moduleId ? iconFor(moduleId) : null;
          }}
        />
      )}
    </Card>
  );
}
