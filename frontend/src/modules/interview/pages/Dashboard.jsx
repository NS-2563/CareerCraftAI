import { useEffect, useState, useCallback, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScoreTooltip } from "@/components/ui/atoms";
import {
  Play,
  History,
  BarChart3,
  ArrowRight,
  Timer,
  Sparkles,
  Target,
  Calendar,
  TrendingUp,
  Trophy,
  FileText,
  MessageSquare,
  BrainCircuit,
  Clock,
  ChevronRight,
  Zap,
  Layers,
} from "lucide-react";

import { useInterviewContext } from "@/modules/interview/context/useInterviewContext";
import { SESSION_STATUS } from "@/modules/interview/services/constants/interviewConstants";
import { getProgress } from "@/modules/interview/services/interviewProgressApi";
import { listSessions } from "@/modules/interview/services/interviewSessionApi";

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

function AnimatedStat({ value, children }) {
  const animated = useCountUp(value);
  const display = animated != null ? String(animated) : value;
  return children(display);
}

function formatDate(isoStr) {
  if (!isoStr) return "\u2014";
  try {
    const d = new Date(isoStr);
    const now = new Date();
    const diffMs = now - d;
    const diffDays = Math.floor(diffMs / 86400000);
    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return "\u2014";
  }
}

function MiniStatCard({ icon: Icon, label, value, sub, trend, tooltip }) {
  const isNum = typeof value === "number" || /^\d+$/.test(String(value));
  const numVal = isNum ? Number(value) : null;
  return (
    <div className="group relative overflow-hidden rounded-xl border border-border/50 bg-card p-4 transition-all duration-200 hover:shadow-lg hover:shadow-primary/5 hover:-translate-y-0.5">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
      <div className="relative flex items-start gap-3">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary/10 to-primary/5">
          <Icon className="size-4.5 text-primary" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium text-muted-foreground">{label}</p>
          {tooltip ? (
            <ScoreTooltip description={tooltip}>
              <div className="mt-0.5 flex cursor-help items-baseline gap-1.5">
                <span className="text-xl font-bold tracking-tight tabular-nums">
                  {isNum ? <AnimatedStat value={numVal}>{v => v}</AnimatedStat> : value}
                </span>
                {trend && (
                  <span className={`text-[11px] font-medium ${trend === "up" ? "text-emerald-500" : trend === "down" ? "text-red-500" : "text-muted-foreground"}`}>
                    {trend === "up" ? "\u2191" : trend === "down" ? "\u2193" : "\u2192"}
                  </span>
                )}
              </div>
            </ScoreTooltip>
          ) : (
            <div className="mt-0.5 flex items-baseline gap-1.5">
              <span className="text-xl font-bold tracking-tight tabular-nums">
                {isNum ? <AnimatedStat value={numVal}>{v => v}</AnimatedStat> : value}
              </span>
              {trend && (
                <span className={`text-[11px] font-medium ${trend === "up" ? "text-emerald-500" : trend === "down" ? "text-red-500" : "text-muted-foreground"}`}>
                  {trend === "up" ? "\u2191" : trend === "down" ? "\u2193" : "\u2192"}
                </span>
              )}
            </div>
          )}
          {sub && <p className="mt-0.5 text-[11px] text-muted-foreground truncate">{sub}</p>}
        </div>
      </div>
    </div>
  );
}

function QuickActionCard({ icon: Icon, title, desc, to, gradient }) {
  return (
    <Link to={to} className="group block">
      <div className="relative overflow-hidden rounded-xl border border-border/50 bg-card p-5 transition-all duration-300 hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-1 hover:border-primary/20">
        <div className={`absolute inset-0 bg-gradient-to-br ${gradient ?? "from-primary/[0.03] to-transparent"} opacity-0 group-hover:opacity-100 transition-opacity duration-200`} />
        <div className="relative flex items-start gap-4">
          <div className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary/10 to-primary/5 ring-1 ring-primary/10 transition-all duration-300 group-hover:ring-primary/30 group-hover:scale-105">
            <Icon className="size-5 text-primary" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold">{title}</p>
            <p className="mt-0.5 text-xs text-muted-foreground leading-relaxed">{desc}</p>
          </div>
          <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/5 opacity-0 group-hover:opacity-100 transition-all duration-300 group-hover:bg-primary/10">
            <ChevronRight className="size-4 text-primary" />
          </div>
        </div>
      </div>
    </Link>
  );
}

function SessionCard({ session }) {
  const completionPct = session.question_count > 0
    ? Math.round(((session.answers_count ?? 0) / session.question_count) * 100)
    : 0;
  const score = session.overall_score;
  const scoreColor = score >= 70 ? "text-emerald-500" : score >= 40 ? "text-amber-500" : "text-red-500";
  const badgeVariant = score >= 70 ? "default" : score >= 40 ? "secondary" : "outline";
  const scoreLabel = score >= 70 ? "Excellent" : score >= 40 ? "Good" : "Needs Work";
  return (
    <Link to={`/interview/history/${session.id}`} className="group block">
      <div className="relative overflow-hidden rounded-xl border border-border/50 bg-card transition-all duration-300 hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-1 hover:border-primary/20">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
        <div className="relative p-5">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1 space-y-3">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-semibold truncate group-hover:text-primary transition-colors">
                    {session.job_title || "General Practice"}
                  </p>
                  <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4 shrink-0 font-medium">
                    {session.difficulty || "mixed"}
                  </Badge>
                </div>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Calendar className="size-3" />
                    {formatDate(session.created_at)}
                  </span>
                  <span className="flex items-center gap-1">
                    <FileText className="size-3" />
                    {session.question_count} Q
                  </span>
                  {completionPct > 0 && (
                    <span className="flex items-center gap-1">
                      <Clock className="size-3" />
                      {completionPct}%
                    </span>
                  )}
                </div>
              </div>
              {completionPct > 0 && (
                <div className="w-full max-w-36 bg-muted rounded-full h-1.5 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-primary/60 to-primary transition-all duration-250"
                    style={{ width: `${completionPct}%` }}
                  />
                </div>
              )}
            </div>
            <div className="flex flex-col items-center gap-1 shrink-0">
              {score != null && (
                <div className="flex flex-col items-center">
                  <span className={`text-xl font-bold tabular-nums leading-none ${scoreColor}`}>
                    {score}
                  </span>
                  <span className="text-[10px] text-muted-foreground mt-0.5">/100</span>
                  <Badge variant={badgeVariant} className="mt-1.5 text-[10px] px-1.5 py-0 h-4 font-medium">
                    {scoreLabel}
                  </Badge>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}

export default function InterviewDashboardPage() {
  const navigate = useNavigate();
  const { currentSession, sessionStatus } = useInterviewContext();

  const [progress, setProgress] = useState(null);
  const [recentSessions, setRecentSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = useCallback(async () => {
    try {
      const [prog, sess] = await Promise.allSettled([
        getProgress(),
        listSessions({ page: 1, pageSize: 3 }),
      ]);
      if (prog.status === "fulfilled") setProgress(prog.value);
      if (sess.status === "fulfilled") setRecentSessions(sess.value?.data?.items ?? []);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const hasActiveSession =
    currentSession &&
    (sessionStatus === SESSION_STATUS.IN_PROGRESS || sessionStatus === SESSION_STATUS.PAUSED);

  const overview = progress?.overview;
  const totalSessions = overview?.total_sessions ?? 0;
  const avgScore = overview?.average_score;
  const trend = overview?.trend;
  const hasData = totalSessions > 0;

  const lastSession = recentSessions[0];
  const streakDays = null;

  const trendDirection = trend === "improving" ? "up" : trend === "declining" ? "down" : trend === "flat" ? "flat" : null;

  return (
    <div className="mx-auto max-w-6xl animate-in fade-in duration-200">
      <div className="space-y-10">
        {/* Hero Section */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/[0.04] via-primary/[0.02] to-background border border-border/50 p-8 md:p-10">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,hsl(var(--primary)/0.06),transparent_70%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,hsl(var(--primary)/0.03),transparent_50%)]" />
          <div className="relative space-y-6">
            <div className="flex items-center gap-2.5">
              <div className="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary/15 to-primary/5 ring-1 ring-primary/10">
                <Sparkles className="size-4 text-primary" />
              </div>
              <span className="text-xs font-semibold tracking-[0.15em] text-muted-foreground uppercase">
                Interview Prep
              </span>
            </div>
            <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6">
              <div className="max-w-2xl space-y-3">
                <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
                  {hasActiveSession ? "Pick up where you left off" : "Master your next interview"}
                </h1>
                <p className="text-base text-muted-foreground leading-relaxed">
                  Practice with AI-generated questions tailored to your target role, receive instant feedback, and track your improvement over time.
                </p>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                {hasActiveSession ? (
                  <Button onClick={() => navigate("/interview/practice")} size="lg" className="gap-2.5 shadow-lg shadow-primary/20 active:scale-[0.97]">
                    <Timer className="size-4" />
                    Continue Session
                    <ArrowRight className="size-4" />
                  </Button>
                ) : (
                  <Button onClick={() => navigate("/interview")} size="lg" className="gap-2.5 shadow-lg shadow-primary/20 active:scale-[0.97]">
                    <Play className="size-4" />
                    Start Practice
                    <ArrowRight className="size-4" />
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Active Session Banner */}
        {hasActiveSession && (
          <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-primary/10 via-primary/[0.05] to-background border border-primary/20">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_left,hsl(var(--primary)/0.08),transparent_70%)]" />
            <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-5">
              <div className="flex items-start gap-4">
                <div className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-primary/10 ring-1 ring-primary/20">
                  <Timer className="size-5 text-primary" />
                </div>
                <div className="space-y-0.5">
                  <p className="font-semibold">Active Session in Progress</p>
                  <p className="text-sm text-muted-foreground">
                    {currentSession?.questionIds?.length ?? 0} questions &middot;{" "}
                    {currentSession?.difficulty ?? "mixed"} difficulty
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button onClick={() => navigate("/interview")} variant="outline" size="sm">
                  New Session
                </Button>
                <Button onClick={() => navigate("/interview/practice")} size="sm" className="gap-1.5 shadow-md">
                  Resume <ArrowRight className="size-3.5" />
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-28 rounded-xl" />
            ))}
          </div>
        ) : !hasData ? (
          /* Empty State */
          <div className="space-y-8">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <MiniStatCard icon={Trophy} label="Average Score" value="\u2014" />
              <MiniStatCard icon={Target} label="Completed" value="0" />
              <MiniStatCard icon={TrendingUp} label="Practice Streak" value="\u2014" />
              <MiniStatCard icon={Calendar} label="Last Interview" value="\u2014" />
            </div>

            <div className="relative overflow-hidden rounded-2xl border border-border/50 bg-gradient-to-br from-primary/[0.02] via-background to-background">
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,hsl(var(--primary)/0.04),transparent_60%)]" />
              <div className="relative flex flex-col items-center justify-center py-20 px-6 gap-6">
                <div className="flex size-20 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 ring-1 ring-primary/10">
                  <BrainCircuit className="size-10 text-primary/60" />
                </div>
                <div className="text-center space-y-2 max-w-md">
                  <p className="text-xl font-semibold tracking-tight">Ready for your first session?</p>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Start your first AI-powered practice interview. Get real-time feedback and track your progress as you improve.
                  </p>
                </div>
                <Button onClick={() => navigate("/interview")} size="lg" className="gap-2.5 shadow-lg shadow-primary/20 active:scale-[0.97]">
                  <Play className="size-4" />
                  Start Your First Interview
                </Button>
              </div>
            </div>

            <div>
              <h2 className="text-sm font-semibold text-muted-foreground mb-4">Quick Actions</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <QuickActionCard icon={Play} title="Start Interview" desc="Begin a new practice session" to="/interview" gradient="from-primary/10 to-transparent" />
                <QuickActionCard icon={History} title="History" desc="Review past sessions and scores" to="/interview/history" gradient="from-blue-500/10 to-transparent" />
                <QuickActionCard icon={BarChart3} title="Progress Analytics" desc="Track your growth over time" to="/interview/progress" gradient="from-emerald-500/10 to-transparent" />
                <QuickActionCard icon={FileText} title="Resume-Based Interview" desc="Import your resume for tailored questions" to="/interview" gradient="from-amber-500/10 to-transparent" />
              </div>
            </div>
          </div>
        ) : (
          /* Data State */
          <>
            {/* Overall Statistics */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Layers className="size-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold text-muted-foreground">Performance Overview</h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <MiniStatCard
                  icon={Trophy}
                  label="Average Score"
                  value={avgScore != null ? `${Math.round(avgScore)}` : "\u2014"}
                  sub={trend === "improving" ? "Improving" : trend === "declining" ? "Declining" : trend === "flat" ? "Steady" : null}
                  trend={trendDirection}
                  tooltip="The average of your AI-evaluated session scores (0–100) across completed practice and real interviews."
                />
                <MiniStatCard
                  icon={Target}
                  label="Completed"
                  value={String(totalSessions)}
                  sub={totalSessions === 1 ? "session" : `${totalSessions} sessions`}
                />
                <MiniStatCard
                  icon={TrendingUp}
                  label="Practice Streak"
                  value={String(streakDays ?? "\u2014")}
                  sub={streakDays != null ? "consecutive days" : "Start practicing daily"}
                />
                <MiniStatCard
                  icon={Calendar}
                  label="Last Interview"
                  value={lastSession ? formatDate(lastSession.created_at) : "\u2014"}
                  sub={lastSession?.job_title ? `as ${lastSession.job_title}` : null}
                />
              </div>
            </div>

            {/* Main Content: Sessions & Quick Actions */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Recent Sessions */}
              <div className="lg:col-span-2 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="size-4 text-muted-foreground" />
                    <h2 className="text-sm font-semibold text-muted-foreground">Recent Sessions</h2>
                  </div>
                  {recentSessions.length > 0 && (
                    <Link to="/interview/history">
                      <Button variant="ghost" size="sm" className="text-xs gap-1.5 text-muted-foreground hover:text-foreground">
                        View all <ArrowRight className="size-3" />
                      </Button>
                    </Link>
                  )}
                </div>
                {recentSessions.length === 0 ? (
                  <Card>
                    <CardContent className="py-10 text-center">
                      <div className="flex flex-col items-center gap-3">
                        <div className="flex size-12 items-center justify-center rounded-xl bg-muted">
                          <MessageSquare className="size-6 text-muted-foreground/40" />
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm font-medium">No sessions yet</p>
                          <p className="text-xs text-muted-foreground">Complete a practice session to see it here.</p>
                        </div>
                        <Link to="/interview/practice">
                          <Button variant="outline" size="sm" className="mt-1 gap-1.5">
                            <Play className="size-3.5" /> Start a practice session
                          </Button>
                        </Link>
                      </div>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {recentSessions.slice(0, 2).map((s) => (
                      <SessionCard key={s.id} session={s} />
                    ))}
                  </div>
                )}
              </div>

              {/* Quick Actions */}
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <Zap className="size-4 text-muted-foreground" />
                  <h2 className="text-sm font-semibold text-muted-foreground">Quick Actions</h2>
                </div>
                <div className="grid grid-cols-1 gap-3">
                  <QuickActionCard icon={Play} title="Start Interview" desc="Begin a new practice session" to="/interview" gradient="from-primary/10 to-transparent" />
                  <QuickActionCard icon={History} title="History" desc="Review past sessions and answers" to="/interview/history" gradient="from-blue-500/10 to-transparent" />
                  <QuickActionCard icon={BarChart3} title="Progress Analytics" desc="Track scores and trends over time" to="/interview/progress" gradient="from-emerald-500/10 to-transparent" />
                  <QuickActionCard icon={FileText} title="Resume-Based" desc="Import resume for custom questions" to="/interview" gradient="from-amber-500/10 to-transparent" />
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
