/* eslint react-hooks/set-state-in-effect: "off" */
import { useEffect, useMemo, useRef, useState } from "react";

import {
  ChevronLeft,
  ChevronRight,
  SkipForward,
  ArrowRightCircle,
  Loader2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";

import { useInterviewContext } from "@/interview/context/useInterviewContext";

function getAnswerForQuestion(session, questionId) {
  if (!session?.answers?.length || !questionId) return null;
  return session.answers.find((a) => a.questionId === questionId) || null;
}

export default function InterviewPracticePage() {

  const { currentSession, currentQuestion,sessionStatus, navigation, session } =
    useInterviewContext();

  const textareaRef = useRef(null);
  const [localValue, setLocalValue] = useState("");

  const currentIndex = useMemo(() => {
    if (!currentSession?.currentQuestionId) return -1;
    return currentSession.questionIds.indexOf(currentSession.currentQuestionId);
  }, [currentSession]);

  const total = currentSession?.questionIds?.length ?? 0;
  const questionNumber = currentIndex >= 0 ? currentIndex + 1 : 0;

  const existingAnswer = useMemo(() => {
    if (!currentSession?.currentQuestionId) return null;
    return getAnswerForQuestion(currentSession, currentSession.currentQuestionId);
  }, [currentSession]);
  console.log("Current Answer:", existingAnswer);

  useEffect(() => {
  if (!currentSession?.currentQuestionId) {
    setLocalValue("");
    return;
  }

  const answer = getAnswerForQuestion(
    currentSession,
    currentSession.currentQuestionId
  );

  setLocalValue(answer?.answer ?? "");
}, [currentSession?.currentQuestionId, currentSession]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;

    // auto-resize
    el.style.height = "0px";
    el.style.height = `${el.scrollHeight}px`;
  }, [localValue]);

  const [isFinishing, setIsFinishing] = useState(false);

  const completedCount = useMemo(() => {
  if (!currentSession?.questionIds?.length) return 0;

  return currentSession.questionIds.filter((qid) => {
    const answer = getAnswerForQuestion(currentSession, qid);

    return (
      answer &&
      !answer.skipped &&
      answer.answer?.trim().length > 0
    );
  }).length;
}, [currentSession]);

const skippedCount = useMemo(() => {
  if (!currentSession?.questionIds?.length) return 0;

  return currentSession.questionIds.filter((qid) => {
    const answer = getAnswerForQuestion(currentSession, qid);
    return answer?.skipped;
  }).length;
}, [currentSession]);

const remainingCount = useMemo(() => {
  return total - completedCount - skippedCount;
}, [total, completedCount, skippedCount]);

const percentComplete = useMemo(() => {
  if (!total) return 0;
  return Math.round((completedCount / total) * 100);
}, [completedCount, total]);

  // Avoid permanently entering loading state: consider session ready
  // if we have a questionIds array even when currentQuestion is temporarily unresolved.
  const isLoading = !currentSession || !Array.isArray(currentSession.questionIds);




  const canGoPrevious = !!currentSession && currentIndex > 0;
  const canGoNext = !!currentSession && currentIndex >= 0 && currentIndex < total - 1;
  const canFinish = !!currentSession && currentIndex === total - 1 && total > 0;

  function handleSaveCurrentAnswer(nextText) {
    if (!currentSession?.currentQuestionId) return;
    session.submitAnswer({ questionId: currentSession.currentQuestionId, responseText: nextText });
  }

  function handlePrevious() {
    if (!canGoPrevious) return;
    handleSaveCurrentAnswer(localValue);
    navigation.goToPreviousQuestion();
  }

  function handleNext() {
    if (!canGoNext) return;
    handleSaveCurrentAnswer(localValue);
    navigation.goToNextQuestion();
  }

  function handleSkip() {
  navigation.skipCurrentQuestion(localValue);
}

  async function handleFinish() {
    if (!canFinish || isFinishing) return;
    setIsFinishing(true);
    try {
      handleSaveCurrentAnswer(localValue);
      session.finishSession();
      // No navigation to Results in Phase 3.
      session.generateSummary?.();
    } finally {
      setIsFinishing(false);
    }
  }

  const categoryLabel = currentQuestion?.category ?? "";
  const difficultyLabel = currentQuestion?.difficulty ?? "";

  if (isLoading) {
    return (
      <div className="w-full px-2 sm:px-0">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              Loading interview…
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">Preparing questions.</CardContent>
        </Card>
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="w-full px-2 sm:px-0">
        <Card>
          <CardHeader>
            <CardTitle>Empty state</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            No active interview question. Start an interview from the setup wizard.
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="w-full px-2 sm:px-0">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-4">
        <div className="space-y-1">
          <h1 className="text-xl sm:text-2xl font-semibold">Interview Practice</h1>
          <div className="text-sm text-muted-foreground">
            {`Question ${questionNumber} of ${total}`}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {categoryLabel ? <Badge variant="secondary">{categoryLabel}</Badge> : null}
          {difficultyLabel ? <Badge variant="outline">{difficultyLabel}</Badge> : null}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{currentQuestion.prompt}</CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          <div className="space-y-2">
            <div className="flex items-center justify-between gap-2 text-sm">
              <div className="font-medium">Progress</div>
              <div className="text-muted-foreground">
                {completedCount} completed • {skippedCount} skipped • {remainingCount} remaining • {percentComplete}%
              </div>
            </div>
            <Progress value={percentComplete} aria-label="Interview progress" />
          </div>

          <div className="space-y-2">
            <div className="text-sm font-medium">Your answer</div>
            <Textarea
              ref={textareaRef}
              value={localValue}
              onChange={(e) => setLocalValue(e.target.value)}
              placeholder="Write your answer here…"
              className="min-h-28 resize-none"
              aria-label="Answer editor"
            />
            <div className="text-xs text-muted-foreground flex items-center justify-between">
              <span>{sessionStatus === "in_progress" ? "" : ""}</span>
              <span>{localValue.length} characters</span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-2 sm:items-center sm:justify-between">
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" onClick={handlePrevious} disabled={!canGoPrevious}>
                <ChevronLeft className="mr-2 size-4" aria-hidden="true" />
                Previous
              </Button>

              <Button type="button" variant="outline" onClick={handleNext} disabled={!canGoNext}>
                Next
                <ChevronRight className="ml-2 size-4" aria-hidden="true" />
              </Button>

              <Button type="button" variant="secondary" onClick={handleSkip}>
                <SkipForward className="mr-2 size-4" aria-hidden="true" />
                Skip Question
              </Button>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button type="button" onClick={handleFinish} disabled={!canFinish || isFinishing}>
                <ArrowRightCircle className="mr-2 size-4" aria-hidden="true" />
                {isFinishing ? "Finishing…" : "Finish Interview"}
              </Button>
            </div>
          </div>

          <div className="text-xs text-muted-foreground" aria-live="polite">
            Completed: {completedCount}/{total}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}



