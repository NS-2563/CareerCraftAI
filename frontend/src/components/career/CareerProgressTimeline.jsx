import { useQuery } from "@tanstack/react-query";
import { TrendingUp } from "lucide-react";

import analyticsApi from "@/services/analyticsApi";
import { Timeline } from "@/components/ui/atoms";

function formatDate(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return "";
  }
}

export default function CareerProgressTimeline() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["career-readiness-history"],
    queryFn: () =>
      analyticsApi
        .getHistory("career_readiness", 100)
        .then((r) => r.data?.data?.items || []),
    staleTime: 60_000,
  });

  return (
    <section className="rounded-xl border bg-card p-6">
      <div className="mb-4">
        <h2 className="text-2xl font-bold">Career Progress</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Your readiness score each time a career report was generated.
        </p>
      </div>

      {isLoading && (
        <div className="animate-pulse space-y-3">
          <div className="h-4 w-1/3 rounded bg-muted" />
          <div className="h-14 rounded-lg bg-muted" />
          <div className="h-14 rounded-lg bg-muted" />
        </div>
      )}

      {!isLoading && isError && (
        <div className="rounded-lg border border-dashed p-5">
          <p className="text-sm text-muted-foreground">
            Couldn&apos;t load your readiness history right now.
          </p>
        </div>
      )}

      {!isLoading && !isError && data && data.length === 0 && (
        <div className="rounded-lg border border-dashed p-5">
          <p className="text-sm text-muted-foreground">
            No readiness history yet. Generate a career report to start
            tracking your progress over time.
          </p>
        </div>
      )}

      {!isLoading && !isError && data && data.length > 0 && (
        <Timeline
          items={data.map((snapshot) => ({
            id: snapshot.id,
            title: `${Math.round(Number(snapshot.value) || 0)}/100 readiness`,
            subtitle: "Career report snapshot",
            timestamp: formatDate(snapshot.recorded_at),
            accentColor: "var(--brand)",
          }))}
          iconFor={() => TrendingUp}
        />
      )}
    </section>
  );
}
