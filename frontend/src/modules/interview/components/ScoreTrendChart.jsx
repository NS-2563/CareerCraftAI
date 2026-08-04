import { useEffect, useMemo, useState } from "react";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from "recharts";
import {
  LineChart as LineChartIcon,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertCircle,
} from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import analyticsApi from "@/services/analyticsApi";

const TREND_META = {
  improving: { Icon: TrendingUp, label: "Improving", className: "text-emerald-500" },
  declining: { Icon: TrendingDown, label: "Declining", className: "text-red-500" },
  flat: { Icon: Minus, label: "Steady", className: "text-muted-foreground" },
  not_enough_data: { Icon: AlertCircle, label: "Insufficient data", className: "text-muted-foreground" },
};

function TrendText({ trend }) {
  const meta = TREND_META[trend] || TREND_META.not_enough_data;
  const Icon = meta.Icon;
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-semibold ${meta.className}`}>
      <Icon className="size-3.5" />
      {meta.label}
    </span>
  );
}

export default function ScoreTrendChart({ trend }) {
  const [items, setItems] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const resp = await analyticsApi.getHistory("interview_average", 500);
        if (!cancelled) setItems(resp?.data?.data?.items ?? []);
      } catch (err) {
        console.error(err);
        if (!cancelled) setError(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const points = useMemo(
    () =>
      (items ?? []).map((s) => {
        const date = s.recorded_at ? new Date(s.recorded_at) : null;
        return {
          score: s.value,
          label: date ? date.toLocaleDateString(undefined, { month: "short", day: "numeric" }) : "\u2014",
          fullDate: date
            ? date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })
            : "\u2014",
        };
      }),
    [items],
  );

  const averageScore = useMemo(() => {
    if (points.length === 0) return null;
    return points.reduce((sum, p) => sum + p.score, 0) / points.length;
  }, [points]);

  const hasTrend = points.length >= 2;

  return (
    <div className="group relative overflow-hidden rounded-xl border border-border/50 bg-card p-5 transition-all duration-200 hover:shadow-lg hover:shadow-primary/5">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
      <div className="relative space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="flex size-7 items-center justify-center rounded-lg bg-primary/10">
              <LineChartIcon className="size-3.5 text-primary" />
            </div>
            <h2 className="text-sm font-semibold text-muted-foreground">Score Over Time</h2>
          </div>
          <TrendText trend={trend} />
        </div>

        {items === null ? (
          <Skeleton className="h-56 rounded-xl" />
        ) : error ? (
          <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
            Couldn&apos;t load score history.
          </div>
        ) : !hasTrend ? (
          <div className="flex h-40 flex-col items-center justify-center gap-1.5 text-center">
            <AlertCircle className="size-5 text-muted-foreground/60" />
            <p className="text-sm font-semibold text-muted-foreground">Not enough data yet</p>
            <p className="text-xs text-muted-foreground/70 max-w-xs">
              Score a few more completed sessions to unlock your score-over-time trend.
            </p>
          </div>
        ) : (
          <div>
            <p className="text-[11px] text-muted-foreground/70 mb-3">
              Average interview score per completed session.
            </p>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={points} margin={{ top: 8, right: 16, left: -8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 11, fill: "#64748b" }}
                  tickLine={false}
                  axisLine={{ stroke: "#e2e8f0" }}
                  minTickGap={24}
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fontSize: 11, fill: "#64748b" }}
                  tickLine={false}
                  axisLine={false}
                  width={40}
                />
                <Tooltip
                  formatter={(value) => [`${value}`, "Average interview score"]}
                  labelFormatter={(label, payload) => payload?.[0]?.payload?.fullDate || label}
                  contentStyle={{
                    borderRadius: 10,
                    border: "1px solid hsl(var(--border))",
                    background: "hsl(var(--popover))",
                    fontSize: 12,
                  }}
                />
                <ReferenceLine
                  y={Math.round(averageScore)}
                  stroke="#94a3b8"
                  strokeDasharray="4 4"
                  label={{
                    value: `Avg ${Math.round(averageScore)}`,
                    position: "insideTopRight",
                    fontSize: 10,
                    fill: "#64748b",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#3b82f6"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: "#3b82f6", strokeWidth: 0 }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
