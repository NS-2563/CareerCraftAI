import { useEffect, useState, useCallback, useMemo, useRef } from "react";

import { Skeleton } from "@/components/ui/skeleton";

function useCountUp(target, duration = 250) {
  const [value, setValue] = useState(0);
  const prevTarget = useRef(0);
  const valueRef = useRef(0);
  useEffect(() => {
    if (target == null || target === prevTarget.current) return;
    prevTarget.current = target;
    const start = performance.now();
    const from = valueRef.current;
    const delta = target - from;
    if (delta === 0) return;
    let raf;
    function tick(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const next = Math.round(from + delta * progress);
      valueRef.current = next;
      setValue(next);
      if (progress < 1) raf = requestAnimationFrame(tick);
    }
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return target != null ? value : null;
}
import {
  TrendingUp,
  TrendingDown,
  Minus,
  BarChart3,
  Target,
  BrainCircuit,
  AlertCircle,
  Layers,
  Trophy,
  Lightbulb,
  ListChecks,
  Users,
  Clock,
  FileText,
  MessageSquare,
  Play,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

import { getProgress } from "@/modules/interview/services/interviewProgressApi";
import ScoreTrendChart from "@/modules/interview/components/ScoreTrendChart";
import { ScoreTooltip } from "@/components/ui/atoms";

function TrendBadge({ trend, size = "sm" }) {
  if (trend === "improving") {
    return (
      <span className={`inline-flex items-center gap-1 font-semibold ${size === "sm" ? "text-xs" : "text-sm"} text-emerald-500`}>
        <TrendingUp className={size === "sm" ? "size-3.5" : "size-4"} />
        Improving
      </span>
    );
  }
  if (trend === "declining") {
    return (
      <span className={`inline-flex items-center gap-1 font-semibold ${size === "sm" ? "text-xs" : "text-sm"} text-red-500`}>
        <TrendingDown className={size === "sm" ? "size-3.5" : "size-4"} />
        Declining
      </span>
    );
  }
  if (trend === "flat") {
    return (
      <span className={`inline-flex items-center gap-1 font-semibold ${size === "sm" ? "text-xs" : "text-sm"} text-muted-foreground`}>
        <Minus className={size === "sm" ? "size-3.5" : "size-4"} />
        Steady
      </span>
    );
  }
  return (
    <span className={`inline-flex items-center gap-1 font-semibold ${size === "sm" ? "text-xs" : "text-sm"} text-muted-foreground`}>
      <AlertCircle className={size === "sm" ? "size-3.5" : "size-4"} />
      Insufficient data
    </span>
  );
}

function ScoreRing({ score, size = 80 }) {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const animatedScore = useCountUp(score ?? 0);
  const displayScore = score != null ? animatedScore : score;
  const offset = circumference - ((displayScore ?? 0) / 100) * circumference;
  const color = score >= 70 ? "#22c55e" : score >= 40 ? "#f59e0b" : "#ef4444";
  const label = score >= 70 ? "Excellent" : score >= 40 ? "Good" : "Needs Work";
  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative inline-flex items-center justify-center shrink-0" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="hsl(var(--muted))" strokeWidth={4} />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={4}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            className="transition-all duration-250 ease-out"
          />
        </svg>
        <span className="absolute text-xl font-bold tabular-nums">{displayScore != null ? Math.round(displayScore) : "\u2014"}</span>
      </div>
      {score != null && (
        <span className={`text-[11px] font-semibold ${score >= 70 ? "text-emerald-500" : score >= 40 ? "text-amber-500" : "text-red-500"}`}>
          {label}
        </span>
      )}
    </div>
  );
}

function MiniStatCard({ icon: Icon, label, value, sub, trend, color }) {
  const isNum = typeof value === "number" || /^\d+$/.test(String(value));
  const numVal = isNum ? Number(value) : null;
  const animated = useCountUp(numVal);
  const display = numVal != null ? animated : value;
  return (
    <div className="group relative overflow-hidden rounded-xl border border-border/50 bg-card p-4 md:p-5 transition-all duration-200 hover:shadow-lg hover:shadow-primary/5 hover:-translate-y-0.5">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
      <div className="relative space-y-2.5">
        <div className="flex items-center justify-between">
          <div className={`flex size-9 items-center justify-center rounded-xl ${color ?? "bg-muted"}`}>
            <Icon className={`size-4.5 ${color ? "text-white" : "text-muted-foreground"}`} />
          </div>
          {trend && <TrendBadge trend={trend} />}
        </div>
        <div>
          <p className="text-xl md:text-2xl font-bold tracking-tight tabular-nums">{display}</p>
          <p className="text-xs text-muted-foreground mt-0.5">{label}</p>
        </div>
        {sub && <p className="text-[10px] text-muted-foreground/70">{sub}</p>}
      </div>
    </div>
  );
}

function CategoryCard({ cat }) {
  const color = cat.average_score >= 70
    ? { bg: "from-emerald-500/20 to-emerald-500/5", text: "text-emerald-600", bar: "linear-gradient(90deg, #22c55e, #16a34a)" }
    : cat.average_score >= 40
      ? { bg: "from-amber-500/20 to-amber-500/5", text: "text-amber-600", bar: "linear-gradient(90deg, #f59e0b, #d97706)" }
      : { bg: "from-red-500/20 to-red-500/5", text: "text-red-600", bar: "linear-gradient(90deg, #ef4444, #dc2626)" };

  return (
    <div className="group relative overflow-hidden rounded-xl border border-border/50 bg-card p-4 transition-all duration-200 hover:shadow-lg hover:shadow-primary/5 hover:-translate-y-0.5">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
      <div className="relative space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold">{cat.category}</p>
          <span className={`text-sm font-bold tabular-nums ${cat.average_score != null ? color.text : "text-muted-foreground"}`}>
            {cat.average_score != null ? `${cat.average_score}` : "\u2014"}
          </span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-250 ease-out"
            style={{ width: `${cat.average_score ?? 0}%`, background: cat.average_score != null ? color.bar : "#6b7280" }}
          />
        </div>
        <div className="flex items-center justify-between text-[10px] text-muted-foreground">
          <span>{cat.question_count} question{cat.question_count !== 1 ? "s" : ""} answered</span>
          {cat.average_score != null && cat.average_score < 50 && (
            <span className="flex items-center gap-0.5 text-amber-600">
              <AlertCircle className="size-3" />
              Needs attention
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

const CATEGORY_ICONS = {
  Technical: BrainCircuit,
  Behavioral: Users,
  HR: FileText,
  Communication: MessageSquare,
  Aptitude: Layers,
};

const SORT_OPTIONS = [
  { value: "score_asc", label: "Score: Low to High" },
  { value: "score_desc", label: "Score: High to Low" },
  { value: "recent", label: "Most Recent" },
  { value: "session_count", label: "Most Sessions" },
];

export default function InterviewProgressPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sort, setSort] = useState("score_asc");

  const fetchProgress = useCallback(async (s) => {
    try {
      const resp = await getProgress(s);
      setData(resp);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProgress(sort).catch(() => setData(null));
  }, [sort, fetchProgress]);

  const overview = data?.overview;
  const byRole = useMemo(() => data?.by_role ?? [], [data]);
  const byCategory = useMemo(() => data?.by_category ?? [], [data]);
  const hasData = overview && overview.total_sessions > 0;

  const bestRole = useMemo(() => {
    if (byRole.length === 0) return null;
    return byRole.reduce((best, curr) =>
      (curr.average_score ?? 0) > (best.average_score ?? 0) ? curr : best
    , byRole[0]);
  }, [byRole]);

  const weakCategories = useMemo(() => {
    return byCategory.filter((c) => c.average_score != null && c.average_score < 50);
  }, [byCategory]);

  const aiRecommendations = useMemo(() => {
    const recs = [];

    if (byCategory.length > 0) {
      const weakest = byCategory.reduce((worst, curr) =>
        (curr.average_score ?? 100) < (worst.average_score ?? 100) ? curr : worst
      , byCategory[0]);
      if (weakest.average_score != null && weakest.average_score < 60) {
        recs.push(`Focus on improving your "${weakest.category}" skills. Practice more ${weakest.category.toLowerCase()} questions to build confidence.`);
      }
    }

    if (byRole.length > 0) {
      const roleCounts = byRole.map((r) => r.session_count);
      const leastPracticed = byRole.find((r) => r.session_count === Math.min(...roleCounts));
      if (leastPracticed && leastPracticed.session_count < 3) {
        recs.push(`You've only practiced "${leastPracticed.job_role || leastPracticed.job_role_normalized}" ${leastPracticed.session_count} time${leastPracticed.session_count !== 1 ? "s" : ""}. More sessions here could reveal growth opportunities.`);
      }
    }

    if (overview?.trend === "declining") {
      recs.push("Your scores are trending downward. Consider reviewing past evaluations and focusing on identified weak areas before your next session.");
    }

    if (overview?.trend === "improving") {
      recs.push("You're on an upward trend! Keep practicing consistently to maintain momentum.");
    }

    if (recs.length === 0 && hasData) {
      recs.push("Great work staying consistent! Try exploring new roles or difficulty levels to challenge yourself further.");
    }

    return recs;
  }, [byCategory, byRole, overview, hasData]);

  return (
    <div className="mx-auto max-w-5xl space-y-10 animate-in fade-in duration-200">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/[0.04] via-primary/[0.02] to-background border border-border/50 p-8 md:p-10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,hsl(var(--primary)/0.06),transparent_70%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,hsl(var(--primary)/0.03),transparent_50%)]" />
        <div className="relative space-y-4">
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary/15 to-primary/5 ring-1 ring-primary/10">
              <BarChart3 className="size-4 text-primary" />
            </div>
            <span className="text-xs font-semibold tracking-[0.15em] text-muted-foreground uppercase">Analytics</span>
          </div>
          <div className="space-y-2">
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Progress Analytics</h1>
            <p className="text-base text-muted-foreground max-w-xl leading-relaxed">
              Track your interview performance across roles, categories, and time. Identify strengths and areas for improvement.
            </p>
          </div>
        </div>
      </div>

      {/* Loading */}
      {loading && !data ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
      ) : !hasData ? (
        /* Empty State */
        <div className="relative overflow-hidden rounded-2xl border border-border/50 bg-gradient-to-br from-primary/[0.02] via-background to-background">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,hsl(var(--primary)/0.04),transparent_60%)]" />
          <div className="relative flex flex-col items-center justify-center py-20 px-6 gap-5">
            <div className="flex size-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 ring-1 ring-primary/10">
              <Target className="size-8 text-primary/60" />
            </div>
            <div className="text-center space-y-2 max-w-sm">
              <p className="text-lg font-semibold tracking-tight">Not enough data yet</p>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Complete a few practice sessions to unlock your performance analytics and insights.
              </p>
            </div>
            <Link to="/interview/practice">
              <Button variant="outline" size="sm" className="gap-1.5">
                <Play className="size-3.5" /> Start a practice session
              </Button>
            </Link>
          </div>
        </div>
      ) : (
        <>
          {/* Top Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="group relative overflow-hidden rounded-xl border border-border/50 bg-card p-5 md:p-6 transition-all duration-200 hover:shadow-lg hover:shadow-primary/5">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
              <div className="relative flex flex-col items-center gap-2">
                <ScoreTooltip description="The average of your AI-evaluated session scores (0–100) across completed practice and real interviews.">
                  <ScoreRing score={overview.average_score} size={80} />
                </ScoreTooltip>
                <p className="text-xs text-muted-foreground mt-1">Average Score</p>
              </div>
            </div>
            <MiniStatCard
              icon={Layers}
              label="Total Sessions"
              value={String(overview.total_sessions)}
              sub={`${overview.total_sessions === 1 ? "session completed" : `${overview.total_sessions} sessions completed`}`}
              color="bg-primary"
            />
            <MiniStatCard
              icon={Trophy}
              label="Best Performing Role"
              value={bestRole ? (bestRole.job_role || bestRole.job_role_normalized) : "\u2014"}
              sub={bestRole ? `${bestRole.session_count} session${bestRole.session_count !== 1 ? "s" : ""}, ${bestRole.average_score != null ? `${Math.round(bestRole.average_score)} avg` : "no score"}` : null}
              trend={bestRole?.trend}
              color="bg-amber-500"
            />
            <MiniStatCard
              icon={TrendingUp}
              label="Current Trend"
              value={overview.trend === "improving" ? "Up" : overview.trend === "declining" ? "Down" : overview.trend === "flat" ? "Steady" : "\u2014"}
              trend={overview.trend}
              color={overview.trend === "improving" ? "bg-emerald-500" : overview.trend === "declining" ? "bg-red-500" : "bg-muted"}
            />
          </div>

          {/* Score Over Time */}
          <ScoreTrendChart trend={overview.trend} />

          {/* Role Performance */}
          {byRole.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Users className="size-4 text-muted-foreground" />
                  <h2 className="text-sm font-semibold text-muted-foreground">Role Performance</h2>
                </div>
                <select
                  value={sort}
                  onChange={(e) => setSort(e.target.value)}
                  className="h-8 rounded-lg border border-input bg-transparent px-2.5 py-1 text-xs outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 cursor-pointer"
                >
                  {SORT_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {byRole.map((role) => {
                  const scoreColor = role.average_score >= 70
                    ? "text-emerald-500"
                    : role.average_score >= 40
                      ? "text-amber-500"
                      : "text-red-500";
                  return (
                    <div key={role.job_role_normalized} className="group relative overflow-hidden rounded-xl border border-border/50 bg-card p-4 transition-all duration-200 hover:shadow-lg hover:shadow-primary/5 hover:-translate-y-0.5">
                      <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                      <div className="relative space-y-3">
                        <div className="flex items-start justify-between">
                          <div className="min-w-0 space-y-1">
                            <p className="text-sm font-semibold truncate">{role.job_role || role.job_role_normalized}</p>
                            <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                              <span className="flex items-center gap-0.5">
                                <BarChart3 className="size-3" />
                                {role.session_count} session{role.session_count !== 1 ? "s" : ""}
                              </span>
                              {role.last_practiced_at && (
                                <span className="flex items-center gap-0.5">
                                  <Clock className="size-3" />
                                  {new Date(role.last_practiced_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex flex-col items-end gap-1 shrink-0">
                            <span className={`text-lg font-bold tabular-nums ${role.average_score != null ? scoreColor : "text-muted-foreground"}`}>
                              {role.average_score != null ? Math.round(role.average_score) : "\u2014"}
                            </span>
                            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Avg</span>
                          </div>
                        </div>
                        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-250"
                            style={{
                              width: `${role.average_score ?? 0}%`,
                              background: role.average_score >= 70
                                ? "linear-gradient(90deg, #22c55e, #16a34a)"
                                : role.average_score >= 40
                                  ? "linear-gradient(90deg, #f59e0b, #d97706)"
                                  : "linear-gradient(90deg, #6b7280, #4b5563)",
                            }}
                          />
                        </div>
                        <TrendBadge trend={role.trend} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Category Breakdown */}
          {byCategory.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <ListChecks className="size-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold text-muted-foreground">Category Breakdown</h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {byCategory.map((cat) => (
                  <CategoryCard key={cat.category} cat={cat} />
                ))}
              </div>
            </div>
          )}

          {/* Weak Areas */}
          {weakCategories.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="size-4 text-amber-500" />
                <h2 className="text-sm font-semibold text-muted-foreground">Weak Areas</h2>
                <span className="text-[11px] text-muted-foreground/60">Scores below 50</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {weakCategories.map((cat) => {
                  const Icon = CATEGORY_ICONS[cat.category] || BrainCircuit;
                  return (
                    <div key={cat.category} className="relative overflow-hidden rounded-xl border border-amber-500/20 bg-gradient-to-br from-amber-500/[0.03] to-transparent p-4 space-y-2">
                      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,hsl(var(--amber-500)/0.04),transparent_60%)]" />
                      <div className="relative flex items-start gap-3">
                        <div className="flex size-9 items-center justify-center rounded-lg bg-amber-500/10">
                          <Icon className="size-4.5 text-amber-500" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-semibold">{cat.category}</p>
                            <span className="text-sm font-bold text-amber-500 tabular-nums">{cat.average_score}/100</span>
                          </div>
                          <div className="h-1.5 bg-muted rounded-full overflow-hidden mt-2">
                            <div className="h-full rounded-full bg-gradient-to-r from-amber-500 to-amber-600" style={{ width: `${cat.average_score}%` }} />
                          </div>
                          <p className="text-[11px] text-muted-foreground mt-1.5">{cat.question_count} question{cat.question_count !== 1 ? "s" : ""} answered</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* AI Recommendations */}
          {aiRecommendations.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <BrainCircuit className="size-4 text-primary" />
                <h2 className="text-sm font-semibold text-muted-foreground">AI Recommendations</h2>
              </div>
              <div className="relative overflow-hidden rounded-xl border border-primary/10 bg-gradient-to-br from-primary/[0.03] to-transparent">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,hsl(var(--primary)/0.04),transparent_60%)]" />
                <div className="relative p-5 space-y-3">
                  {aiRecommendations.map((rec, i) => (
                    <div key={i} className="flex items-start gap-3">
                      <div className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-primary/10 mt-0.5">
                        <Lightbulb className="size-3.5 text-primary" />
                      </div>
                      <p className="text-sm text-muted-foreground leading-relaxed">{rec}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
