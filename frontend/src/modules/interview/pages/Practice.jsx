import { useEffect, useMemo, useRef, useState } from "react";

import {
  ChevronLeft,
  ChevronRight,
  SkipForward,
  Flag,
  Loader2,
  CheckCircle2,
  Lightbulb,
  TrendingUp,
  MessageSquare,
  Timer,
  Clock,
  Zap,
  Sparkles,
  Sparkle,
  BrainCircuit,
  BookOpen,
  Target,
  Save,
  Quote,
  ListChecks,
  Star,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { ScoreTooltip } from "@/components/ui/atoms";

import { useInterviewContext } from "@/modules/interview/context/useInterviewContext";

function getAnswerForQuestion(session, questionId) {
  if (!session?.answers?.length || !questionId) return null;
  return session.answers.find((a) => a.questionId === questionId) || null;
}

function ScoreRing({ score, size = 56 }) {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - ((score ?? 0) / 100) * circumference;
  const color = score >= 70 ? "#22c55e" : score >= 40 ? "#f59e0b" : "#ef4444";
  return (
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
      <span className="absolute text-sm font-bold tabular-nums">{score}</span>
    </div>
  );
}

const STAR_TIPS = [
  { label: "S \u2014 Situation", text: "Set the context and background. Describe a specific situation you were in." },
  { label: "T \u2014 Task", text: "Explain the task or challenge you needed to accomplish." },
  { label: "A \u2014 Action", text: "Describe the specific actions you took to address the situation." },
  { label: "R \u2014 Result", text: "Share the outcomes and results of your actions, using metrics where possible." },
];

const COMMUNICATION_TIPS = [
  "Structure answers with a clear beginning, middle, and end",
  "Use specific examples rather than generalizations",
  "Pause before answering to collect your thoughts",
  "Keep answers concise \u2014 aim for 60\u201390 seconds",
];

const COMMON_MISTAKES = [
  "Being too vague \u2014 provide concrete details",
  "Not quantifying results with numbers or metrics",
  "Rambling without a clear structure",
  "Focusing on \u2018we\u2019 instead of \u2018I\u2019 and your contribution",
];

export default function InterviewPracticePage() {
  const { currentSession, currentQuestion, navigation, session } =
    useInterviewContext();

  const textareaRef = useRef(null);
  const [localValue, setLocalValue] = useState("");
  const [savedIndicator, setSavedIndicator] = useState(false);
  const [prevQuestionId, setPrevQuestionId] = useState(
    currentSession?.currentQuestionId ?? null
  );

  if ((currentSession?.currentQuestionId ?? null) !== prevQuestionId) {
    setPrevQuestionId(currentSession?.currentQuestionId ?? null);
    const answer = currentSession?.currentQuestionId
      ? getAnswerForQuestion(currentSession, currentSession.currentQuestionId)
      : null;
    setLocalValue(answer?.answer ?? "");
  }

  const currentIndex = useMemo(() => {
    if (!currentSession?.currentQuestionId) return -1;
    return currentSession.questionIds.indexOf(currentSession.currentQuestionId);
  }, [currentSession]);

  const total = currentSession?.questionIds?.length ?? 0;
  const questionNumber = currentIndex >= 0 ? currentIndex + 1 : 0;

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = `${el.scrollHeight}px`;
  }, [localValue]);

  const [isFinishing, setIsFinishing] = useState(false);

  const completedCount = useMemo(() => {
    if (!currentSession?.questionIds?.length) return 0;
    return currentSession.questionIds.filter((qid) => {
      const answer = getAnswerForQuestion(currentSession, qid);
      return answer && !answer.skipped && answer.answer?.trim().length > 0;
    }).length;
  }, [currentSession]);

  const skippedCount = useMemo(() => {
    if (!currentSession?.questionIds?.length) return 0;
    return currentSession.questionIds.filter((qid) => {
      const answer = getAnswerForQuestion(currentSession, qid);
      return answer?.skipped;
    }).length;
  }, [currentSession]);

  const remainingCount = useMemo(() => total - completedCount - skippedCount, [total, completedCount, skippedCount]);

  const percentComplete = useMemo(() => {
    if (!total) return 0;
    return Math.round((completedCount / total) * 100);
  }, [completedCount, total]);

  const isLoading = !currentSession || !Array.isArray(currentSession.questionIds);

  const canGoPrevious = !!currentSession && currentIndex > 0;
  const canGoNext = !!currentSession && currentIndex >= 0 && currentIndex < total - 1;
  const canFinish = !!currentSession && currentIndex === total - 1 && total > 0;

  function handleSaveCurrentAnswer(nextText) {
    if (!currentSession?.currentQuestionId) return;
    session.submitAnswer({ questionId: currentSession.currentQuestionId, responseText: nextText });
  }

  function triggerAutoSave(text) {
    if (!currentSession?.currentQuestionId) return;
    session.submitAnswer({ questionId: currentSession.currentQuestionId, responseText: text });
    setSavedIndicator(true);
    setTimeout(() => setSavedIndicator(false), 2000);
  }

  function handlePrevious() {
    if (!canGoPrevious) return;
    triggerEvaluation(localValue);
    handleSaveCurrentAnswer(localValue);
    navigation.goToPreviousQuestion();
    setTimeout(() => session.persistSessionUpdate(), 0);
  }

  function handleNext() {
    if (!canGoNext) return;
    triggerEvaluation(localValue);
    handleSaveCurrentAnswer(localValue);
    navigation.goToNextQuestion();
    setTimeout(() => session.persistSessionUpdate(), 0);
  }

  function handleSkip() {
    triggerEvaluation(localValue);
    navigation.skipCurrentQuestion(localValue);
    setTimeout(() => session.persistSessionUpdate(), 0);
  }

  async function handleFinish() {
    if (!canFinish || isFinishing) return;
    setIsFinishing(true);
    try {
      triggerEvaluation(localValue);
      handleSaveCurrentAnswer(localValue);
      const completedAt = new Date().toISOString();
      session.persistSessionUpdate({ completed_at: completedAt });
      session.finishSession();
      session.generateSummary?.();
    } finally {
      setIsFinishing(false);
    }
  }

  const currentEvaluation = useMemo(() => {
    if (!currentSession?.evaluations?.length || !currentSession?.currentQuestionId) return null;
    return currentSession.evaluations.find((e) => e.questionId === currentSession.currentQuestionId) || null;
  }, [currentSession]);

  const [evaluating, setEvaluating] = useState(false);

  function triggerEvaluation(text) {
    if (evaluating || !currentSession?.currentQuestionId || !text?.trim()) return;
    if (currentEvaluation) return;
    setEvaluating(true);
    session
      .evaluateAnswer(
        currentSession.currentQuestionId,
        text,
        currentSession.jobTitle ?? currentSession.jobRole ?? null,
        currentSession.difficulty ?? null,
      )
      .finally(() => setEvaluating(false));
  }

  const categoryLabel = currentQuestion?.category ?? "";
  const difficultyLabel = currentQuestion?.difficulty ?? "";

  const timerMode = currentSession?.timerMode ?? "off";

  if (isLoading) {
    return (
      <div className="mx-auto max-w-2xl pt-12">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 gap-3">
            <Loader2 className="size-5 animate-spin text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Loading questions\u2026</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="mx-auto max-w-2xl pt-12">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 gap-2">
            <MessageSquare className="size-6 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">No active question. Start from the dashboard.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl animate-in fade-in duration-200">
      <div className="space-y-6">
        {/* Top Bar */}
        <div className="space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary/10 to-primary/5 ring-1 ring-primary/10">
                <Sparkles className="size-4 text-primary" />
              </div>
              <div>
                <p className="text-xs font-semibold tracking-wider text-muted-foreground">
                  Question <span className="tabular-nums">{questionNumber}</span> of <span className="tabular-nums">{total}</span>
                </p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {categoryLabel && (
                <Badge variant="secondary" className="gap-1 text-xs font-medium">
                  <BookOpen className="size-3" />
                  {categoryLabel}
                </Badge>
              )}
              {difficultyLabel && (
                <Badge variant="outline" className="gap-1 text-xs">
                  <Sparkle className="size-3" />
                  {difficultyLabel}
                </Badge>
              )}
              {timerMode !== "off" && (
                <Badge variant="outline" className="gap-1 text-xs text-muted-foreground">
                  <Timer className="size-3" />
                  {timerMode === "per_question" ? "Per Q" : "Session"}
                </Badge>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-primary/60 to-primary transition-all duration-250"
                style={{ width: `${percentComplete}%` }}
              />
            </div>
            <div className="flex items-center gap-1.5 shrink-0">
              <span className="text-xs font-semibold tabular-nums">{completedCount}</span>
              <span className="text-xs text-muted-foreground">/ {total}</span>
            </div>
            <div className="flex items-center gap-1 shrink-0 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-0.5">
                <CheckCircle2 className="size-3 text-emerald-500" />
                {completedCount}
              </span>
              <span className="text-border">|</span>
              <span className="inline-flex items-center gap-0.5">
                <SkipForward className="size-3 text-amber-500" />
                {skippedCount}
              </span>
              <span className="text-border">|</span>
              <span className="inline-flex items-center gap-0.5">
                <Clock className="size-3 text-muted-foreground" />
                {remainingCount}
              </span>
            </div>
          </div>
        </div>

        {/* Main Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Question Area */}
          <div className="lg:col-span-2 space-y-5">
            {/* Question Card */}
            <div className="relative overflow-hidden rounded-xl border border-border/50 bg-card transition-all duration-200">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.02] to-transparent pointer-events-none" />
              <div className="relative p-6 md:p-7 space-y-5">
                <div className="space-y-3">
                  {categoryLabel && (
                    <Badge variant="secondary" className="gap-1.5 text-[11px] px-2.5 py-1 font-medium rounded-lg">
                      <ListChecks className="size-3" />
                      {categoryLabel} Question
                    </Badge>
                  )}
                  <h2 className="text-xl md:text-2xl font-semibold tracking-tight leading-snug">
                    {currentQuestion.prompt}
                  </h2>
                </div>

                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock className="size-3.5" />
                    Est. <span className="font-medium">2\u20133 min</span> to answer
                  </span>
                </div>
              </div>
            </div>

            {/* Answer Editor */}
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
                  <MessageSquare className="size-3.5" />
                  Your Answer
                </label>
                <div className="flex items-center gap-2">
                  {savedIndicator && (
                    <span className="text-[11px] text-emerald-500 flex items-center gap-1 animate-in fade-in duration-200">
                      <Save className="size-3" />
                      Saved
                    </span>
                  )}
                  <span className="text-[11px] text-muted-foreground tabular-nums">{localValue.length} chars</span>
                </div>
              </div>
              <div className="relative rounded-xl border border-border/50 bg-card transition-all duration-200 focus-within:border-primary/40 focus-within:ring-1 focus-within:ring-primary/10">
                <Textarea
                  ref={textareaRef}
                  value={localValue}
                  onChange={(e) => setLocalValue(e.target.value)}
                  onBlur={() => triggerAutoSave(localValue)}
                  placeholder="Type your answer here. Use the STAR method to structure your response..."
                  className="min-h-40 resize-none text-sm leading-relaxed border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 shadow-none p-5"
                  aria-label="Answer editor"
                />
              </div>
            </div>

            {/* Navigation */}
            <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="default"
                  onClick={handlePrevious}
                  disabled={!canGoPrevious}
                  className="gap-1.5"
                >
                  <ChevronLeft className="size-4" />
                  Previous
                </Button>
                <Button
                  variant="ghost"
                  size="default"
                  onClick={handleSkip}
                  className="gap-1.5 text-muted-foreground hover:text-foreground"
                >
                  <SkipForward className="size-4" />
                  Skip
                </Button>
                <Button
                  variant="outline"
                  size="default"
                  onClick={handleNext}
                  disabled={!canGoNext}
                  className="gap-1.5"
                >
                  Next
                  <ChevronRight className="size-4" />
                </Button>
              </div>
              <Button
                onClick={handleFinish}
                disabled={!canFinish || isFinishing}
                size="default"
                className="gap-1.5 shadow-lg shadow-primary/20 active:scale-[0.97]"
              >
                {isFinishing ? (
                  <><Loader2 className="size-4 animate-spin" />Finishing\u2026</>
                ) : (
                  <><Flag className="size-4" />Finish Interview</>
                )}
              </Button>
            </div>

            {/* Evaluating indicator */}
            {evaluating && (
              <div className="flex items-center gap-2 px-1">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1.5">
                    <div className="flex size-2 rounded-full bg-primary/40 animate-pulse" />
                    <div className="flex size-2 rounded-full bg-primary/40 animate-pulse" style={{ animationDelay: "0.2s" }} />
                    <div className="flex size-2 rounded-full bg-primary/40 animate-pulse" style={{ animationDelay: "0.4s" }} />
                  </div>
                  AI is analyzing your answer\u2026
                </div>
              </div>
            )}

            {/* AI Feedback Panel */}
            {currentEvaluation && !currentEvaluation.evaluation_failed ? (
              <div className="animate-in fade-in slide-in-from-bottom-2 duration-200">
                <div className="relative overflow-hidden rounded-xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/[0.03] to-transparent">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/[0.03] rounded-full -translate-y-1/2 translate-x-1/2" />
                  <div className="relative p-6 space-y-5">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary/10 to-primary/5 ring-1 ring-primary/10">
                          <BrainCircuit className="size-4.5 text-primary" />
                        </div>
                        <div>
                          <p className="text-sm font-semibold">AI Feedback</p>
                          <p className="text-[11px] text-muted-foreground">Real-time evaluation</p>
                        </div>
                      </div>
                      <ScoreTooltip description="AI evaluation of this answer on a 0–100 scale, based on the job role, question, and your response.">
                        <ScoreRing score={currentEvaluation.score} size={56} />
                      </ScoreTooltip>
                    </div>

                    {/* Score Bar */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">Score</span>
                        <span className="font-semibold tabular-nums">
                          {currentEvaluation.score}/100
                        </span>
                      </div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-250 ease-out"
                          style={{
                            width: `${currentEvaluation.score}%`,
                            background: currentEvaluation.score >= 70
                              ? "linear-gradient(90deg, #22c55e, #16a34a)"
                              : currentEvaluation.score >= 40
                                ? "linear-gradient(90deg, #f59e0b, #d97706)"
                                : "linear-gradient(90deg, #ef4444, #dc2626)",
                          }}
                        />
                      </div>
                    </div>

                    {/* Strengths & Improvements */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                      {currentEvaluation.strengths?.length > 0 && (
                        <div className="space-y-3">
                          <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-500">
                            <TrendingUp className="size-3.5" />
                            Strengths
                          </div>
                          <ul className="space-y-2">
                            {currentEvaluation.strengths.map((s, i) => (
                              <li key={i} className="text-xs text-muted-foreground flex items-start gap-2 leading-relaxed">
                                <span className="mt-1 block size-1.5 shrink-0 rounded-full bg-emerald-500/60" />
                                {s}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {currentEvaluation.improvements?.length > 0 && (
                        <div className="space-y-3">
                          <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-600 dark:text-amber-500">
                            <Lightbulb className="size-3.5" />
                            Areas to Improve
                          </div>
                          <ul className="space-y-2">
                            {currentEvaluation.improvements.map((s, i) => (
                              <li key={i} className="text-xs text-muted-foreground flex items-start gap-2 leading-relaxed">
                                <span className="mt-1 block size-1.5 shrink-0 rounded-full bg-amber-500/60" />
                                {s}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* Model Answer */}
                    {currentEvaluation.model_answer_notes && (
                      <div className="rounded-xl bg-muted/50 p-4 space-y-2 border border-border/30">
                        <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                          <Quote className="size-3.5" />
                          Model Answer Note
                        </div>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          {currentEvaluation.model_answer_notes}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : currentEvaluation?.evaluation_failed ? (
              <div className="rounded-xl border border-dashed border-border/60 p-5 text-xs text-muted-foreground text-center bg-muted/20">
                <span className="flex items-center justify-center gap-2">
                  <BrainCircuit className="size-4 text-muted-foreground/50" />
                  Answer evaluation was unavailable for this response.
                </span>
              </div>
            ) : null}
          </div>

          {/* Right Sidebar - Tips */}
          <div className="hidden lg:block space-y-4">
            <div className="sticky top-24 space-y-4">
              {/* Progress Mini */}
              <Card>
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
                    <Target className="size-3.5" />
                    Session Progress
                  </div>
                  <div className="space-y-2.5">
                    {[
                      { label: "Answered", value: completedCount, color: "text-emerald-500" },
                      { label: "Skipped", value: skippedCount, color: "text-amber-500" },
                      { label: "Remaining", value: remainingCount, color: "text-muted-foreground" },
                    ].map((item) => (
                      <div key={item.label} className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">{item.label}</span>
                        <span className={`font-semibold tabular-nums ${item.color}`}>{item.value}</span>
                      </div>
                    ))}
                    <div className="border-t border-border/50 pt-2.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">Total Questions</span>
                        <span className="font-semibold tabular-nums">{total}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* STAR Method */}
              <Card>
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
                    <Star className="size-3.5" />
                    STAR Method
                  </div>
                  <div className="space-y-2">
                    {STAR_TIPS.map((tip) => (
                      <div key={tip.label} className="text-xs space-y-0.5">
                        <p className="font-medium text-foreground/80">{tip.label}</p>
                        <p className="text-muted-foreground leading-relaxed">{tip.text}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Communication Tips */}
              <Card>
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
                    <MessageSquare className="size-3.5" />
                    Communication Tips
                  </div>
                  <ul className="space-y-1.5">
                    {COMMUNICATION_TIPS.map((tip, i) => (
                      <li key={i} className="text-xs text-muted-foreground flex items-start gap-1.5 leading-relaxed">
                        <span className="mt-1 block size-1 shrink-0 rounded-full bg-primary/40" />
                        {tip}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              {/* Common Mistakes */}
              <Card>
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
                    <Zap className="size-3.5" />
                    Common Mistakes
                  </div>
                  <ul className="space-y-1.5">
                    {COMMON_MISTAKES.map((tip, i) => (
                      <li key={i} className="text-xs text-muted-foreground flex items-start gap-1.5 leading-relaxed">
                        <span className="mt-1 block size-1 shrink-0 rounded-full bg-amber-500/50" />
                        {tip}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
