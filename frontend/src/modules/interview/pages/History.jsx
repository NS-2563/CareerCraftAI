import { useEffect, useState, useCallback, useMemo } from "react";
import { useNavigate, Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  History,
  ChevronLeft,
  ChevronRight,
  Eye,
  ArrowRight,
  Search,
  Calendar,
  FileText,
  Clock,
  Sparkles,
  ArrowUpDown,
  X,
  BrainCircuit,
} from "lucide-react";

import { listSessions } from "@/modules/interview/services/interviewSessionApi";
import { useInterviewContext } from "@/modules/interview/context/useInterviewContext";
import { SESSION_STATUS } from "@/modules/interview/services/constants/interviewConstants";

function formatDate(isoStr) {
  if (!isoStr) return "\u2014";
  try {
    const d = new Date(isoStr);
    const now = new Date();
    const diffMs = now - d;
    const diffDays = Math.floor(diffMs / 86400000);
    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    return d.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return isoStr;
  }
}

function formatTime(isoStr) {
  if (!isoStr) return "";
  try {
    const d = new Date(isoStr);
    return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

function getScoreColor(score) {
  if (score == null) return "text-muted-foreground";
  return score >= 70 ? "text-emerald-500" : score >= 40 ? "text-amber-500" : "text-red-500";
}

function getScoreBadgeStyle(score) {
  if (score == null) return "bg-muted text-muted-foreground border-border";
  return score >= 70
    ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
    : score >= 40
      ? "bg-amber-500/10 text-amber-600 border-amber-500/20"
      : "bg-red-500/10 text-red-600 border-red-500/20";
}

function getScoreLabel(score) {
  if (score == null) return "No Score";
  return score >= 70 ? "Excellent" : score >= 40 ? "Good" : "Needs Work";
}

function getDifficultyColor(difficulty) {
  if (!difficulty) return "bg-muted text-muted-foreground";
  const d = difficulty.toLowerCase();
  if (d === "easy") return "bg-emerald-500/10 text-emerald-600";
  if (d === "medium") return "bg-amber-500/10 text-amber-600";
  if (d === "hard") return "bg-red-500/10 text-red-600";
  return "bg-muted text-muted-foreground";
}

const FILTER_OPTIONS = [
  { value: "all", label: "All Sessions" },
  { value: "completed", label: "Completed" },
  { value: "in_progress", label: "In Progress" },
];

export default function InterviewHistoryPage() {
  const navigate = useNavigate();
  const { currentSession, sessionStatus } = useInterviewContext();

  const [sessions, setSessions] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");
  const [sortOrder, setSortOrder] = useState("newest");

  const fetchSessions = useCallback(async (p) => {
    try {
      const resp = await listSessions({ page: p, pageSize: 10 });
      setSessions(resp?.data?.items ?? []);
      setPagination(resp?.data?.pagination ?? null);
    } finally {
      setLoading(false);
    }
  }, []);

  const [prevPage, setPrevPage] = useState(page);

  if (page !== prevPage) {
    setPrevPage(page);
    setLoading(true);
  }

  useEffect(() => {
    fetchSessions(page).catch(() => {
      setSessions([]);
      setPagination(null);
    });
  }, [page, fetchSessions]);

  const filteredSessions = useMemo(() => {
    let result = [...sessions];

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter((s) =>
        (s.job_title ?? "").toLowerCase().includes(q)
      );
    }

    if (activeFilter === "completed") {
      result = result.filter((s) => s.overall_score != null);
    } else if (activeFilter === "in_progress") {
      result = result.filter((s) => s.overall_score == null);
    }

    if (sortOrder === "newest") {
      result.sort((a, b) => new Date(b.created_at ?? 0) - new Date(a.created_at ?? 0));
    } else if (sortOrder === "oldest") {
      result.sort((a, b) => new Date(a.created_at ?? 0) - new Date(b.created_at ?? 0));
    } else if (sortOrder === "score_high") {
      result.sort((a, b) => (b.overall_score ?? -1) - (a.overall_score ?? -1));
    } else if (sortOrder === "score_low") {
      result.sort((a, b) => (a.overall_score ?? -1) - (b.overall_score ?? -1));
    }

    return result;
  }, [sessions, searchQuery, activeFilter, sortOrder]);

  const hasActiveSession =
    currentSession &&
    (sessionStatus === SESSION_STATUS.IN_PROGRESS ||
      sessionStatus === SESSION_STATUS.PAUSED);

  return (
    <div className="mx-auto max-w-4xl space-y-8 animate-in fade-in duration-200">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/[0.04] via-primary/[0.02] to-background border border-border/50 p-8 md:p-10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,hsl(var(--primary)/0.06),transparent_70%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,hsl(var(--primary)/0.03),transparent_50%)]" />
        <div className="relative flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6">
          <div className="space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary/15 to-primary/5 ring-1 ring-primary/10">
                <History className="size-4 text-primary" />
              </div>
              <span className="text-xs font-semibold tracking-[0.15em] text-muted-foreground uppercase">
                History
              </span>
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-bold tracking-tight">Practice History</h1>
              <p className="text-base text-muted-foreground max-w-xl leading-relaxed">
                Review your past interview sessions, compare scores, and track your growth over time.
              </p>
            </div>
          </div>
          <div className="shrink-0">
            {hasActiveSession ? (
              <Button onClick={() => navigate("/interview/practice")} variant="default" size="lg" className="gap-2 shadow-lg shadow-primary/20">
                Return to Active Session
                <ArrowRight className="size-4" />
              </Button>
            ) : (
              <Button onClick={() => navigate("/interview")} variant="default" size="lg" className="gap-2 shadow-lg shadow-primary/20 active:scale-[0.97]">
                Start New Practice
                <ArrowRight className="size-4" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by role..."
            className="pl-9 h-10"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="size-4" />
            </button>
          )}
        </div>
        <div className="flex gap-2">
          <div className="flex rounded-xl border border-border/60 bg-muted/30 p-0.5" role="radiogroup">
            {FILTER_OPTIONS.map((o) => {
              const selected = activeFilter === o.value;
              return (
                <button
                  key={o.value}
                  type="button"
                  role="radio"
                  aria-checked={selected}
                  onClick={() => setActiveFilter(o.value)}
                  className={
                    "rounded-lg px-3 py-1.5 text-xs font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
                    (selected
                      ? "bg-background text-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground")
                  }
                >
                  {o.label}
                </button>
              );
            })}
          </div>
          <div className="relative">
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="h-10 rounded-xl border border-border/60 bg-muted/30 px-3 py-1.5 text-xs font-medium text-muted-foreground outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 appearance-none cursor-pointer hover:text-foreground transition-colors"
            >
              <option value="newest">Newest</option>
              <option value="oldest">Oldest</option>
              <option value="score_high">Score: High to Low</option>
              <option value="score_low">Score: Low to High</option>
            </select>
            <ArrowUpDown className="absolute right-2.5 top-1/2 -translate-y-1/2 size-3 pointer-events-none text-muted-foreground" />
          </div>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="grid grid-cols-1 gap-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
      ) : filteredSessions.length === 0 ? (
        <div className="relative overflow-hidden rounded-2xl border border-border/50 bg-gradient-to-br from-primary/[0.02] via-background to-background">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,hsl(var(--primary)/0.04),transparent_60%)]" />
          <div className="relative flex flex-col items-center justify-center py-20 px-6 gap-5">
            <div className="flex size-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 ring-1 ring-primary/10">
              <BrainCircuit className="size-8 text-primary/60" />
            </div>
            <div className="text-center space-y-2 max-w-sm">
              <p className="text-lg font-semibold tracking-tight">
                {searchQuery || activeFilter !== "all"
                  ? "No sessions match your search"
                  : "No sessions yet"}
              </p>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {searchQuery || activeFilter !== "all"
                  ? "Try adjusting your search or filter to find what you're looking for."
                  : "Complete a practice interview or log a real interview to see your history here."}
              </p>
            </div>
            {!searchQuery && activeFilter === "all" && (
              <Button onClick={() => navigate("/interview")} size="lg" className="gap-2 shadow-lg shadow-primary/20 active:scale-[0.97]">
                <Sparkles className="size-4" />
                Start Your First Interview
              </Button>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              {filteredSessions.length} session{filteredSessions.length !== 1 ? "s" : ""}
              {(searchQuery || activeFilter !== "all") && (
                <span className="text-muted-foreground/60">
                  {" "}filtered
                </span>
              )}
            </p>
          </div>

          {filteredSessions.map((s) => {
            const isReal = s.session_type === "real_interview";
            const completionPct = s.question_count > 0
              ? Math.round(((s.answers_count ?? 0) / s.question_count) * 100)
              : 0;
            const score = isReal ? s.self_rated_confidence : s.overall_score;

            return (
              <Link
                key={s.id}
                to={`/interview/history/${s.id}`}
                className="group block"
              >
                <div className="relative overflow-hidden rounded-xl border border-border/50 bg-card transition-all duration-200 hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-0.5 hover:border-primary/20">
                  <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                  <div className="relative p-5">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                      <div className="min-w-0 flex-1 space-y-3">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-base font-semibold truncate group-hover:text-primary transition-colors">
                            {s.job_title || "General Practice"}
                          </p>
                          {s.difficulty && (
                            <span className={`inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] font-semibold ${getDifficultyColor(s.difficulty)}`}>
                              {s.difficulty}
                            </span>
                          )}
                          {isReal && (
                            <span className="inline-flex items-center rounded-md bg-primary/10 text-primary border border-primary/20 px-1.5 py-0.5 text-[10px] font-semibold">
                              Real Interview
                            </span>
                          )}
                          {score != null && (
                            <span className={`inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-semibold ${getScoreBadgeStyle(score)}`}>
                              {score}/100
                            </span>
                          )}
                        </div>

                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Calendar className="size-3.5" />
                            {formatDate(s.created_at)}
                          </span>
                          {formatTime(s.created_at) && (
                            <span className="text-muted-foreground/60">{formatTime(s.created_at)}</span>
                          )}
                          {!isReal && (
                            <span className="flex items-center gap-1">
                              <FileText className="size-3.5" />
                              {s.question_count} question{s.question_count !== 1 ? "s" : ""}
                            </span>
                          )}
                          {isReal && (
                            <span className="flex items-center gap-1">
                              <Clock className="size-3.5" />
                              Retrospective log
                            </span>
                          )}
                          {completionPct > 0 && (
                            <span className="flex items-center gap-1">
                              <Clock className="size-3.5" />
                              {completionPct}% complete
                            </span>
                          )}
                        </div>

                        {completionPct > 0 && (
                          <div className="w-full max-w-48 bg-muted rounded-full h-1.5 overflow-hidden">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-primary/60 to-primary transition-all duration-250"
                              style={{ width: `${completionPct}%` }}
                            />
                          </div>
                        )}
                      </div>

                      <div className="flex sm:flex-col items-center sm:items-end gap-3 sm:gap-2 shrink-0">
                        {score != null && (
                          <div className="flex items-center sm:items-end gap-2 sm:flex-col">
                            <span className={`text-lg font-bold tabular-nums leading-none ${getScoreColor(score)}`}>
                              {score}
                              <span className="text-[10px] text-muted-foreground font-normal">/100</span>
                            </span>
                            <span className={`text-[10px] font-semibold ${getScoreColor(score)}`}>
                              {isReal ? "Confidence" : getScoreLabel(score)}
                            </span>
                          </div>
                        )}
                        {score == null && !isReal && (
                          <Badge variant="outline" className="text-[10px] gap-1">
                            <Clock className="size-3" />
                            In Progress
                          </Badge>
                        )}
                        <Button variant="outline" size="sm" className="gap-1.5 group/btn">
                          <Eye className="size-3.5 transition-transform group-hover/btn:scale-110" />
                          <span className="hidden sm:inline">Review</span>
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            );
          })}

          {/* Pagination */}
          {pagination && pagination.total_pages > 1 && (
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4 pb-2">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!pagination.has_prev}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="gap-1"
                >
                  <ChevronLeft className="size-3.5" />
                  Previous
                </Button>

                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(pagination.total_pages, 5) }, (_, i) => {
                    const pageNum = (() => {
                      const total = pagination.total_pages;
                      const current = pagination.page;
                      if (total <= 5) return i + 1;
                      if (current <= 3) return i + 1;
                      if (current >= total - 2) return total - 4 + i;
                      return current - 2 + i;
                    })();
                    return (
                      <button
                        key={pageNum}
                        type="button"
                        onClick={() => setPage(pageNum)}
                        className={
                          "size-8 rounded-lg text-xs font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
                          (pageNum === pagination.page
                            ? "bg-primary text-primary-foreground shadow-sm"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground")
                        }
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  disabled={!pagination.has_next}
                  onClick={() => setPage((p) => p + 1)}
                  className="gap-1"
                >
                  Next
                  <ChevronRight className="size-3.5" />
                </Button>
              </div>

              <span className="text-xs text-muted-foreground tabular-nums">
                Page {pagination.page} of {pagination.total_pages}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
