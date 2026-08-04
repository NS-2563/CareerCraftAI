import { useMemo, useEffect, useState, useRef } from "react";
import { useSearchParams, useParams, useNavigate } from "react-router-dom";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ScoreTooltip } from "@/components/ui/atoms";

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
  Lightbulb,
  MessageSquare,
  CheckCircle2,
  Clock,
  ChevronDown,
  ChevronUp,
  Sparkles,
  BarChart3,
  RotateCcw,
  History,
  Download,
  BrainCircuit,
  Target,
  Quote,
  Zap,
  FileText,
} from "lucide-react";

import { useInterviewContext } from "@/modules/interview/context/useInterviewContext";
import { getSession } from "@/modules/interview/services/interviewSessionApi";

function formatDurationMs(durationMs) {
  if (!durationMs || typeof durationMs !== "number" || durationMs < 0) return "\u2014";
  const totalSeconds = Math.floor(durationMs / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
}

function ScoreRing({ score, size = 100 }) {
  const radius = (size - 10) / 2;
  const circumference = 2 * Math.PI * radius;
  const animatedScore = useCountUp(score ?? 0);
  const displayScore = score != null ? animatedScore : score;
  const offset = circumference - ((displayScore ?? 0) / 100) * circumference;
  const color = score >= 70 ? "#22c55e" : score >= 40 ? "#f59e0b" : "#ef4444";
  const label = score >= 70 ? "Excellent" : score >= 40 ? "Good" : "Needs Work";
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative inline-flex items-center justify-center shrink-0" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="hsl(var(--muted))" strokeWidth={5} />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={5}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-250 ease-out"
          />
        </svg>
        <span className="absolute text-2xl font-bold tabular-nums">{displayScore}</span>
      </div>
      <span className={`text-xs font-semibold ${score >= 70 ? "text-emerald-500" : score >= 40 ? "text-amber-500" : "text-red-500"}`}>
        {label}
      </span>
    </div>
  );
}

function MiniStatCard({ icon: Icon, label, value, sub, color }) {
  const isNum = typeof value === "number" || /^\d+$/.test(String(value).replace(/%$/, ""));
  const numVal = isNum ? Number(String(value).replace("%", "")) : null;
  const animated = useCountUp(numVal);
  const display = numVal != null ? (String(value).includes("%") ? `${animated}%` : animated) : value;
  return (
    <div className="group relative overflow-hidden rounded-xl border border-border/50 bg-card p-4 md:p-5 transition-all duration-200 hover:shadow-lg hover:shadow-primary/5 hover:-translate-y-0.5">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
      <div className="relative space-y-2">
        <div className="flex items-center justify-between">
          <div className={`flex size-8 items-center justify-center rounded-lg ${color ?? "bg-muted"}`}>
            <Icon className={`size-4 ${color ? "text-white" : "text-muted-foreground"}`} />
          </div>
        </div>
        <div>
          <p className="text-lg md:text-xl font-bold tracking-tight tabular-nums">{display}</p>
          <p className="text-[11px] text-muted-foreground">{label}</p>
        </div>
        {sub && <p className="text-[10px] text-muted-foreground/70">{sub}</p>}
      </div>
    </div>
  );
}

function QuestionCard({ question, index, defaultOpen }) {
  const [open, setOpen] = useState(defaultOpen);
  const isAnswered = !question.skipped && String(question.answerText ?? "").trim().length > 0;
  const isSkipped = Boolean(question.skipped);
  const evalData = question.evaluation && !question.evaluation.evaluation_failed ? question.evaluation : null;

  const statusLabel = isSkipped ? "Skipped" : isAnswered ? "Answered" : "Unanswered";
  const statusColor = isSkipped
    ? "bg-amber-500/10 text-amber-600 border-amber-500/20"
    : isAnswered
      ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
      : "bg-muted text-muted-foreground border-border";

  return (
    <div className="rounded-xl border border-border/50 bg-card transition-all duration-200 hover:shadow-md hover:shadow-primary/5">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-4 p-5 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-xl"
        aria-expanded={open}
      >
        <div className="min-w-0 flex-1 space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="flex size-6 items-center justify-center rounded-md bg-muted text-[11px] font-bold text-muted-foreground">
              {index + 1}
            </span>
            {question.category && (
              <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4 font-medium">
                {question.category}
              </Badge>
            )}
            <span className={`inline-flex items-center rounded-md border px-1.5 py-0 text-[10px] font-semibold ${statusColor}`}>
              {statusLabel}
            </span>
          </div>
          <p className="text-sm font-medium leading-relaxed line-clamp-2">{question.prompt}</p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {evalData && (
            <span className={`text-sm font-bold tabular-nums ${evalData.score >= 70 ? "text-emerald-500" : evalData.score >= 40 ? "text-amber-500" : "text-red-500"}`}>
              {evalData.score}
              <span className="text-[10px] text-muted-foreground font-normal">/100</span>
            </span>
          )}
          {open ? <ChevronUp className="size-4 text-muted-foreground" /> : <ChevronDown className="size-4 text-muted-foreground" />}
        </div>
      </button>

      {open && (
        <div className="animate-in fade-in slide-in-from-top-1 duration-200 px-5 pb-5 space-y-4 border-t border-border/50 pt-4">
          {/* Your Answer */}
          <div className="space-y-1.5">
            <p className="text-[11px] font-medium text-muted-foreground flex items-center gap-1">
              <MessageSquare className="size-3" />
              Your Answer
            </p>
            <div className="rounded-lg bg-muted/40 p-3">
              <p className="text-sm whitespace-pre-wrap leading-relaxed">
                {isAnswered ? question.answerText : <span className="italic text-muted-foreground/60">No answer provided</span>}
              </p>
            </div>
          </div>

          {/* AI Feedback */}
          {evalData ? (
            <div className="space-y-4">
              {/* Score Bar */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground flex items-center gap-1">
                    <BrainCircuit className="size-3" />
                    AI Score
                  </span>
                  <span className="font-semibold tabular-nums">{evalData.score}/100</span>
                </div>
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-250 ease-out"
                    style={{
                      width: `${evalData.score}%`,
                      background: evalData.score >= 70
                        ? "linear-gradient(90deg, #22c55e, #16a34a)"
                        : evalData.score >= 40
                          ? "linear-gradient(90deg, #f59e0b, #d97706)"
                          : "linear-gradient(90deg, #ef4444, #dc2626)",
                    }}
                  />
                </div>
              </div>

              {/* Strengths & Improvements */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {evalData.strengths?.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-emerald-600 dark:text-emerald-500 flex items-center gap-1">
                      <TrendingUp className="size-3.5" />
                      Strengths
                    </p>
                    <ul className="space-y-1.5">
                      {evalData.strengths.map((s, i) => (
                        <li key={i} className="text-xs text-muted-foreground flex items-start gap-2 leading-relaxed">
                          <span className="mt-1.5 block size-1 shrink-0 rounded-full bg-emerald-500/60" />
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {evalData.improvements?.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-amber-600 dark:text-amber-500 flex items-center gap-1">
                      <Lightbulb className="size-3.5" />
                      Areas for Improvement
                    </p>
                    <ul className="space-y-1.5">
                      {evalData.improvements.map((s, i) => (
                        <li key={i} className="text-xs text-muted-foreground flex items-start gap-2 leading-relaxed">
                          <span className="mt-1.5 block size-1 shrink-0 rounded-full bg-amber-500/60" />
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Model Answer Notes */}
              {evalData.model_answer_notes && (
                <div className="rounded-xl bg-muted/40 p-3.5 space-y-1.5 border border-border/30">
                  <p className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                    <Quote className="size-3" />
                    Model Answer Note
                  </p>
                  <p className="text-xs text-muted-foreground leading-relaxed">{evalData.model_answer_notes}</p>
                </div>
              )}
            </div>
          ) : question.evaluation?.evaluation_failed ? (
            <p className="text-xs text-muted-foreground italic">AI evaluation was unavailable for this response.</p>
          ) : isAnswered ? (
            <p className="text-xs text-muted-foreground italic">No AI evaluation available for this answer.</p>
          ) : null}
        </div>
      )}
    </div>
  );
}

export default function InterviewResultsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const params = useParams();
  const sessionIdParam = searchParams.get("sessionId") || params.sessionId;

  const { session } = useInterviewContext();

  const [historicalSession, setHistoricalSession] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [prevSessionIdParam, setPrevSessionIdParam] = useState(null);

  if (sessionIdParam !== prevSessionIdParam) {
    setPrevSessionIdParam(sessionIdParam);
    if (!sessionIdParam) {
      setHistoricalSession(null);
    } else {
      setHistoryLoading(true);
    }
  }

  useEffect(() => {
    if (!sessionIdParam) return;
    let cancelled = false;
    getSession(Number(sessionIdParam))
      .then((data) => { if (!cancelled) setHistoricalSession(data); })
      .catch(() => { if (!cancelled) setHistoricalSession(null); })
      .finally(() => { if (!cancelled) setHistoryLoading(false); });
    return () => { cancelled = true; };
  }, [sessionIdParam]);

  const isHistorical = !!sessionIdParam;

  const summary = useMemo(() => {
    if (isHistorical) {
      if (!historicalSession) return null;
      const qs = historicalSession.questions ?? [];
      const ans = historicalSession.answers ?? [];
      const ansMap = {};
      for (const a of ans) ansMap[a.questionId] = a;
      const startedMs = historicalSession.started_at ? new Date(historicalSession.started_at).getTime() : null;
      const completedMs = historicalSession.completed_at ? new Date(historicalSession.completed_at).getTime() : null;
      return {
        sessionId: historicalSession.id,
        jobTitle: historicalSession.job_title,
        difficulty: historicalSession.difficulty,
        overallScore: historicalSession.overall_score,
        startedAtEpochMs: startedMs,
        finishedAtEpochMs: completedMs,
        questions: qs.map((q) => {
          const answer = ansMap[q.id] ?? {};
          return {
            questionId: q.id,
            prompt: q.question ?? "",
            category: q.category ?? "",
            answerText: answer.answer ?? "",
            skipped: answer.skipped ?? false,
            submittedAtEpochMs: answer.answeredAt ?? null,
            evaluation: answer.evaluation ?? null,
          };
        }),
      };
    }
    return session.generateSummary?.() ?? null;
  }, [isHistorical, historicalSession, session]);

  const sessionMeta = summary;
  const summaryQuestions = useMemo(() => sessionMeta?.questions ?? [], [sessionMeta]);

  const total = summaryQuestions.length;
  const skipped = summaryQuestions.filter((q) => q.skipped).length;
  const answered = summaryQuestions.filter((q) => !q.skipped && String(q.answerText ?? "").trim().length > 0).length;
  const completionPct = total > 0 ? Math.round((answered / total) * 100) : 0;

  const evaluatedQuestions = summaryQuestions.filter((q) => q.evaluation && !q.evaluation.evaluation_failed);
  const avgScore = evaluatedQuestions.length > 0
    ? Math.round(evaluatedQuestions.reduce((sum, q) => sum + (q.evaluation?.score ?? 0), 0) / evaluatedQuestions.length)
    : null;

  const durationMs = typeof sessionMeta?.startedAtEpochMs === "number" && typeof sessionMeta?.finishedAtEpochMs === "number"
    ? sessionMeta.finishedAtEpochMs - sessionMeta.startedAtEpochMs
    : null;

  // Category breakdown
  const categoryBreakdown = useMemo(() => {
    const groups = {};
    for (const q of summaryQuestions) {
      if (!q.category) continue;
      if (!groups[q.category]) groups[q.category] = { scores: [], count: 0 };
      groups[q.category].count++;
      if (q.evaluation && !q.evaluation.evaluation_failed) {
        groups[q.category].scores.push(q.evaluation.score);
      }
    }
    return Object.entries(groups).map(([category, data]) => ({
      category,
      count: data.count,
      avgScore: data.scores.length > 0
        ? Math.round(data.scores.reduce((a, b) => a + b, 0) / data.scores.length)
        : null,
    }));
  }, [summaryQuestions]);

  const performanceLabel = avgScore >= 70 ? "Excellent Performance" : avgScore >= 40 ? "Good Effort" : "Needs Improvement";

  if (isHistorical && historyLoading) {
    return (
      <div className="mx-auto max-w-5xl pt-12 space-y-6 animate-in fade-in duration-200">
        <Skeleton className="h-48 rounded-2xl" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-28 rounded-xl" />)}
        </div>
        <Skeleton className="h-64 rounded-xl" />
      </div>
    );
  }

  if (isHistorical && !historicalSession) {
    return (
      <div className="mx-auto max-w-4xl pt-12">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 gap-2">
            <p className="text-sm text-muted-foreground">Session not found.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-10 animate-in fade-in duration-200">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/[0.04] via-primary/[0.02] to-background border border-border/50 p-8 md:p-10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,hsl(var(--primary)/0.06),transparent_70%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,hsl(var(--primary)/0.03),transparent_50%)]" />
        <div className="relative flex flex-col md:flex-row md:items-center md:justify-between gap-8">
          <div className="space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary/15 to-primary/5 ring-1 ring-primary/10">
                <Sparkles className="size-4 text-primary" />
              </div>
              <span className="text-xs font-semibold tracking-[0.15em] text-muted-foreground uppercase">
                {isHistorical ? "Session Review" : "Interview Complete"}
              </span>
            </div>
            <div className="space-y-2">
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
                {isHistorical ? "Session Review" : "You did it!"}
              </h1>
              <p className="text-sm md:text-base text-muted-foreground max-w-lg leading-relaxed">
                {isHistorical && sessionMeta?.jobTitle
                  ? `Reviewing your "${sessionMeta.jobTitle}" practice session.`
                  : "Here\u2019s a detailed breakdown of your performance across all questions."}
              </p>
            </div>
          </div>
          <div className="flex flex-col items-center md:items-end gap-2">
            <ScoreTooltip description="This session's overall score — the average of the AI evaluations (0–100) of each of your answers.">
              <ScoreRing score={avgScore} size={100} />
            </ScoreTooltip>
            <div className="flex items-center gap-1.5 mt-1">
              {avgScore >= 70 ? (
                <TrendingUp className="size-3.5 text-emerald-500" />
              ) : avgScore >= 40 ? (
                <Zap className="size-3.5 text-amber-500" />
              ) : (
                <Target className="size-3.5 text-red-500" />
              )}
              <span className={`text-xs font-medium ${avgScore >= 70 ? "text-emerald-500" : avgScore >= 40 ? "text-amber-500" : "text-red-500"}`}>
                {performanceLabel}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
        <MiniStatCard
          icon={FileText}
          label="Total Questions"
          value={String(total)}
          color="bg-primary"
        />
        <MiniStatCard
          icon={CheckCircle2}
          label="Answered"
          value={String(answered)}
          sub={`${skipped > 0 ? `${skipped} skipped` : ""}`}
          color="bg-emerald-500"
        />
        <MiniStatCard
          icon={Clock}
          label="Duration"
          value={formatDurationMs(durationMs)}
          color="bg-amber-500"
        />
        <MiniStatCard
          icon={Target}
          label="Completion"
          value={`${completionPct}%`}
          color={completionPct >= 80 ? "bg-emerald-500" : completionPct >= 50 ? "bg-amber-500" : "bg-muted"}
        />
      </div>

      {/* Performance Breakdown */}
      {categoryBreakdown.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <BarChart3 className="size-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-muted-foreground">Performance by Category</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {categoryBreakdown.map((cat) => (
              <div key={cat.category} className="rounded-xl border border-border/50 bg-card p-4 space-y-2.5 transition-all duration-200 hover:shadow-md">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">{cat.category}</p>
                  <span className={`text-xs font-semibold tabular-nums ${cat.avgScore >= 70 ? "text-emerald-500" : cat.avgScore >= 40 ? "text-amber-500" : "text-muted-foreground"}`}>
                    {cat.avgScore != null ? `${cat.avgScore}/100` : "\u2014"}
                  </span>
                </div>
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-250 ease-out"
                    style={{
                      width: `${cat.avgScore ?? 0}%`,
                      background: cat.avgScore >= 70
                        ? "linear-gradient(90deg, #22c55e, #16a34a)"
                        : cat.avgScore >= 40
                          ? "linear-gradient(90deg, #f59e0b, #d97706)"
                          : "linear-gradient(90deg, #6b7280, #4b5563)",
                    }}
                  />
                </div>
                <p className="text-[10px] text-muted-foreground">{cat.count} question{cat.count !== 1 ? "s" : ""}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Question Review */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <MessageSquare className="size-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold text-muted-foreground">Question Review</h2>
          <span className="text-[11px] text-muted-foreground/60 ml-auto tabular-nums">{total} question{total !== 1 ? "s" : ""}</span>
        </div>

        {total === 0 ? (
          <Card>
            <CardContent className="py-12 text-center text-sm text-muted-foreground">
              No interview data found.
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {summaryQuestions.map((q, idx) => (
              <QuestionCard key={q.questionId} question={q} index={idx} defaultOpen={idx === 0} />
            ))}
          </div>
        )}
      </div>

      {/* Bottom Actions */}
      <div className="flex flex-wrap items-center justify-center gap-3 pt-4 pb-8">
        <Button
          onClick={() => navigate("/interview")}
          size="lg"
          className="gap-2 shadow-lg shadow-primary/20 active:scale-[0.97]"
        >
          <RotateCcw className="size-4" />
          Practice Again
        </Button>
        <Button
          onClick={() => navigate("/interview/history")}
          variant="outline"
          size="lg"
          className="gap-2"
        >
          <History className="size-4" />
          View History
        </Button>
        <Button
          variant="outline"
          size="lg"
          className="gap-2"
          disabled
        >
          <Download className="size-4" />
          Download Report
        </Button>
      </div>
    </div>
  );
}
