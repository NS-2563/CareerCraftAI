import { useMemo } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";

import { useInterviewContext } from "@/interview/context/useInterviewContext";

function formatEpochMs(epochMs) {
  if (!epochMs || typeof epochMs !== "number") return "—";

  try {
    return new Date(epochMs).toLocaleString();
  } catch {
    return "—";
  }
}

function formatDurationMs(durationMs) {
  if (!durationMs || typeof durationMs !== "number" || durationMs < 0) return "—";

  const totalSeconds = Math.floor(durationMs / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  if (hours > 0) return `${hours}h ${minutes}m ${seconds}s`;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
}

export default function InterviewResultsPage() {
  const { currentSession, questionBank, session } = useInterviewContext();

  const summary = useMemo(() => {
    // Must be presentation-only: compute from existing architecture.
    return session.generateSummary?.() ?? null;
  }, [session, currentSession, questionBank]);

  const sessionMeta = summary;
  const summaryQuestions = sessionMeta?.questions ?? [];

  const total = summaryQuestions.length;
  const skipped = summaryQuestions.filter((q) => q.skipped).length;
  const answered = summaryQuestions.filter((q) => !q.skipped && String(q.answerText ?? "").trim().length > 0)
    .length;

  const completionPct = total > 0 ? Math.round((answered / total) * 100) : 0;
  const durationMs =
    typeof sessionMeta?.startedAtEpochMs === "number" &&
    typeof sessionMeta?.finishedAtEpochMs === "number"
      ? sessionMeta.finishedAtEpochMs - sessionMeta.startedAtEpochMs
      : null;

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-xl sm:text-2xl font-semibold">Interview Results</h1>
        <p className="text-sm text-muted-foreground">Review your responses.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="md:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Session Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div className="text-sm">
                <div className="font-medium">Completion</div>
                <div className="text-muted-foreground">{completionPct}%</div>
              </div>
              <div className="w-44">
                <Progress value={completionPct} aria-label="Session completion" />
              </div>
            </div>

            <Separator />

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="space-y-1">
                <div className="text-sm text-muted-foreground">Total Questions</div>
                <div className="text-base font-semibold">{total}</div>
              </div>
              <div className="space-y-1">
                <div className="text-sm text-muted-foreground">Answered</div>
                <div className="text-base font-semibold">{answered}</div>
              </div>
              <div className="space-y-1">
                <div className="text-sm text-muted-foreground">Skipped</div>
                <div className="text-base font-semibold">{skipped}</div>
              </div>

              <div className="space-y-1 sm:col-span-2">
                <div className="text-sm text-muted-foreground">Started Time</div>
                <div className="text-sm font-medium">{formatEpochMs(sessionMeta?.startedAtEpochMs)}</div>
              </div>
              <div className="space-y-1 sm:col-span-2">
                <div className="text-sm text-muted-foreground">Finished Time</div>
                <div className="text-sm font-medium">{formatEpochMs(sessionMeta?.finishedAtEpochMs)}</div>
              </div>

              <div className="space-y-1 sm:col-span-2">
                <div className="text-sm text-muted-foreground">Duration</div>
                <div className="text-sm font-medium">{formatDurationMs(durationMs)}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Statistics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Total</span>
                <span className="font-medium">{total}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Answered</span>
                <span className="font-medium">{answered}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Skipped</span>
                <span className="font-medium">{skipped}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Completion</span>
                <span className="font-medium">{completionPct}%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Question Review</CardTitle>
        </CardHeader>
        <CardContent>
          {total === 0 ? (
            <div className="text-sm text-muted-foreground">No interview data found.</div>
          ) : (
            <div className="space-y-4">
              {summaryQuestions.map((q, idx) => {
                const isAnswered = !q.skipped && String(q.answerText ?? "").trim().length > 0;
                const isSkipped = Boolean(q.skipped);

                const status = isSkipped
                  ? { label: "Skipped", variant: "secondary" }
                  : isAnswered
                    ? { label: "Answered", variant: "default" }
                    : { label: "Unanswered", variant: "outline" };

                return (
                  <div key={q.questionId} className="space-y-2 rounded-lg border p-4">
                    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                      <div className="space-y-1">
                        <div className="text-sm text-muted-foreground">Question {idx + 1} of {total}</div>
                        <div className="text-sm font-medium">{q.prompt}</div>
                      </div>
                      <Badge variant={status.variant}>{status.label}</Badge>
                    </div>

                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground">User Answer</div>
                      <div className="text-sm whitespace-pre-wrap">
                        {isAnswered ? q.answerText : "—"}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Keep consistent with architecture: presentation-only. */}
    </div>
  );
}




