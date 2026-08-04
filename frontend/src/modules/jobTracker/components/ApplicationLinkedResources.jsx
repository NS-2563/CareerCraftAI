import { useState } from "react";
import {
  Building2,
  Briefcase,
  CalendarDays,
  ChevronDown,
  FileText,
  Send,
  RefreshCw,
  Link2,
  Loader2,
  MessageSquarePlus,
  ClipboardList,
  Check,
  Circle,
  MessagesSquare,
} from "lucide-react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ChecklistProgress, StatusBadge, Skeleton, SuccessBanner, ScoreTooltip } from "@/components/ui/atoms";

import { cn } from "@/lib/utils";

import { useResumes } from "@/hooks/useResumes";
import { useJDMatchResult } from "../hooks/useJDMatchResult";
import { useRecheckMatch } from "../hooks/useRecheckMatch";
import { useUpdateJob } from "../hooks/useUpdateJob";
import { useJobCoverLetters } from "../hooks/useJobCoverLetters";
import { useRealInterviews } from "../hooks/useRealInterviews";
import { useThread } from "@/communication/hooks/useThread";
import { useConversationStatus } from "@/communication/hooks/useConversationStatus";
import { useWorkspace, useDismissWorkspaceInsight } from "../hooks/useWorkspace";

import ApplicationCommunicationThread from "@/communication/components/ApplicationCommunicationThread";
import LinkResumeDialog from "./LinkResumeDialog";
import GenerateCoverLetterDialog from "./GenerateCoverLetterDialog";
import LogRealInterviewDialog from "./LogRealInterviewDialog";
import NextActionBanner from "./NextActionBanner";
import WorkspaceInsights from "./WorkspaceInsights";
import ApplicationActivityFeed from "./ApplicationActivityFeed";

function daysAgo(iso) {
  if (!iso) return "";
  const created = new Date(iso);
  if (Number.isNaN(created.getTime())) return "";
  const days = Math.floor((Date.now() - created.getTime()) / 86400000);
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  return `${days} days ago`;
}

function formatDate(value) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleDateString();
  } catch {
    return "—";
  }
}

function LinkStatus({ label, present, detail }) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-lg border px-2.5 py-2",
        present ? "border-emerald-500/20 bg-emerald-500/5" : "border-border bg-muted/30"
      )}
    >
      {present ? (
        <Check className="size-4 shrink-0 text-emerald-500" strokeWidth={2.5} />
      ) : (
        <Circle className="size-4 shrink-0 text-muted-foreground/40" />
      )}
      <div className="min-w-0">
        <div className="text-xs font-medium">{label}</div>
        <div
          className={cn(
            "truncate text-[11px]",
            present ? "text-emerald-600 dark:text-emerald-400" : "text-muted-foreground"
          )}
        >
          {detail}
        </div>
      </div>
    </div>
  );
}

export default function ApplicationLinkedResources({ job, initialTab = "resume", onTabChange }) {
  const queryClient = useQueryClient();
  const { data: resumes = [], isLoading: resumesLoading } = useResumes();
  const [linkResumeOpen, setLinkResumeOpen] = useState(false);
  const [generateCoverLetterOpen, setGenerateCoverLetterOpen] = useState(false);
  const [logInterviewOpen, setLogInterviewOpen] = useState(false);
  const [jdValue, setJdValue] = useState(job?.job_description ?? "");
  const [savedJd, setSavedJd] = useState((job?.job_description ?? "").trim());
  const [jdSaving, setJdSaving] = useState(false);
  const [prevJobId, setPrevJobId] = useState(job?.id);
  const [tab, setTab] = useState(initialTab);
  const [matchJustRan, setMatchJustRan] = useState(false);

  if (job?.id !== prevJobId) {
    setPrevJobId(job?.id);
    setJdValue(job?.job_description ?? "");
    setSavedJd((job?.job_description ?? "").trim());
    setTab(initialTab);
  }

  const {
    data: matchResult,
    isLoading: matchLoading,
    isError: matchError,
  } = useJDMatchResult(job?.id);

  const { data: threadMessages } = useThread(job?.id);
  const { data: convStatus } = useConversationStatus(job?.id);
  const { data: coverLetters, isLoading: coverLettersLoading } = useJobCoverLetters(job?.id);
  const { data: realInterviews, isLoading: realInterviewsLoading } = useRealInterviews(job?.id);

  const { data: workspace } = useWorkspace(job?.id);
  const {
    mutate: dismissInsight,
    isPending: dismissingInsight,
  } = useDismissWorkspaceInsight(job?.id);

  const nextAction = workspace?.next_action ?? null;
  const workspaceInsights = workspace?.insights ?? [];

  const {
    mutate: updateJob,
    isPending: linkingResume,
  } = useUpdateJob();

  const {
    mutate: recheck,
    isPending: rechecking,
    error: recheckError,
  } = useRecheckMatch();

  const linkedResume = resumes.find((r) => Number(r.id) === Number(job?.resume_id));

  const jdDirty = jdValue.trim() !== savedJd;
  const hasJd = Boolean(savedJd);

  const coverLetterCount = Array.isArray(coverLetters) ? coverLetters.length : 0;
  const interviewCount = Array.isArray(realInterviews) ? realInterviews.length : 0;
  const threadCount = Array.isArray(threadMessages) ? threadMessages.length : 0;

  const readinessItems = [
    { label: "Resume linked", done: Boolean(linkedResume) },
    { label: "Cover letter created", done: coverLetterCount > 0 },
    { label: "JD match recorded", done: Boolean(matchResult) },
    { label: "Communication started", done: threadCount > 0 },
    { label: "Interview logged", done: interviewCount > 0 },
  ];

  function saveJd(onSaved) {
    setJdSaving(true);
    updateJob(
      { id: job.id, data: { job_description: jdValue } },
      {
        onSuccess: () => {
          setSavedJd(jdValue.trim());
          toast.success("Job description saved");
          queryClient.invalidateQueries({ queryKey: ["workspace", job.id] });
          onSaved?.();
        },
        onError: (err) => {
          toast.error(
            err?.response?.data?.message ||
              err?.response?.data?.detail ||
              err?.message ||
              "Failed to save the job description."
          );
        },
        onSettled: () => setJdSaving(false),
      }
    );
  }

  function runMatch() {
    const onSuccess = () => {
      setMatchJustRan(true);
      queryClient.invalidateQueries({ queryKey: ["workspace", job.id] });
    };
    if (jdDirty) {
      saveJd(() => recheck({ jobId: job.id }, { onSuccess }));
    } else {
      recheck({ jobId: job.id }, { onSuccess });
    }
  }

  function handleTabChange(next) {
    setTab(next);
    onTabChange?.(next);
  }

  return (
    <div>
      {/* ------------------------------------------------------------------
         Sticky header: company, role, applied date, link status row
      ------------------------------------------------------------------ */}
      <div className="sticky top-0 z-10 border-b border-border/60 bg-popover/95 px-6 pt-6 pb-4 backdrop-blur">
        <div className="flex items-start justify-between gap-3 pr-12">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <Building2 className="size-4 shrink-0 text-muted-foreground" />
              <h2 className="truncate font-heading text-lg font-semibold leading-tight">
                {job?.company || "Untitled company"}
              </h2>
            </div>
            <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
              <Briefcase className="size-3.5 shrink-0" />
              <span className="truncate">{job?.job_title || "Untitled role"}</span>
            </div>
            <div className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
              <CalendarDays className="size-3.5 shrink-0" />
              <span>
                Applied{daysAgo(job?.created_at) ? ` • ${daysAgo(job?.created_at)}` : ""}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge status={job?.status} />
            {convStatus?.status ? (
              <StatusBadge status={convStatus.status} />
            ) : null}
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-5">
          <LinkStatus
            label="Resume"
            present={Boolean(linkedResume)}
            detail={linkedResume ? "Linked" : "Not linked"}
          />
          <LinkStatus
            label="Cover Letter"
            present={coverLetterCount > 0}
            detail={coverLetterCount > 0 ? `${coverLetterCount} letter${coverLetterCount > 1 ? "s" : ""}` : "Not created"}
          />
          <LinkStatus
            label="JD Match"
            present={Boolean(matchResult)}
            detail={matchResult ? `${Math.round(matchResult.match_score)}%` : "No match"}
          />
          <LinkStatus
            label="Communication"
            present={threadCount > 0}
            detail={threadCount > 0 ? `${threadCount} message${threadCount > 1 ? "s" : ""}` : "No messages"}
          />
          <LinkStatus
            label="Interview"
            present={interviewCount > 0}
            detail={interviewCount > 0 ? "Logged" : "Not logged"}
          />
        </div>
      </div>

      {/* ------------------------------------------------------------------
         Body: next action -> insights -> readiness + section tabs
      ------------------------------------------------------------------ */}
      <div className="px-6 pt-4 pb-6">
        {nextAction ? (
          <NextActionBanner action={nextAction} onNavigate={handleTabChange} />
        ) : null}

        <div className={nextAction ? "mt-3" : ""}>
          <WorkspaceInsights
            insights={workspaceInsights}
            onDismiss={dismissingInsight ? undefined : (key) => dismissInsight(key)}
          />
        </div>

        <ChecklistProgress
          label="Application Readiness"
          items={readinessItems}
          className={nextAction || workspaceInsights.length ? "mt-5" : ""}
        />

        <Tabs value={tab} onValueChange={handleTabChange} className="mt-5 w-full">
          <TabsList className="w-full justify-start overflow-x-auto">
            <TabsTrigger value="resume">
              <FileText className="size-4" />
              Resume
            </TabsTrigger>
            <TabsTrigger value="cover-letter">
              <Send className="size-4" />
              Cover Letter
            </TabsTrigger>
            <TabsTrigger value="jd-match">
              <ClipboardList className="size-4" />
              JD Match
            </TabsTrigger>
            <TabsTrigger value="communication">
              <MessagesSquare className="size-4" />
              Communication
            </TabsTrigger>
            <TabsTrigger value="interview">
              <MessageSquarePlus className="size-4" />
              Interview
            </TabsTrigger>
          </TabsList>

          {/* ---------------------------- Resume ---------------------------- */}
          <TabsContent value="resume" className="pt-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Resume Used
                </CardTitle>
                <CardDescription>The resume linked to this application.</CardDescription>
              </CardHeader>
              <CardContent>
                {linkedResume ? (
                  <div className="flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <div className="truncate font-medium">{linkedResume.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {linkedResume.completed ? "Completed" : "Draft"}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button type="button" variant="outline" size="sm" asChild>
                        <a href={`/resume-studio?id=${linkedResume.id}`}>Open</a>
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setLinkResumeOpen(true)}
                      >
                        Change
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-start gap-3">
                    <p className="text-sm text-muted-foreground">
                      No resume linked to this application yet. Linking one lets the cover letter
                      and JD match features use it automatically.
                    </p>
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={() => setLinkResumeOpen(true)}
                      disabled={resumesLoading || linkingResume}
                    >
                      <Link2 className="mr-2 h-4 w-4" />
                      {resumesLoading ? "Loading..." : "Link a Resume"}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ------------------------- Cover Letter ------------------------- */}
          <TabsContent value="cover-letter" className="space-y-4 pt-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Send className="h-4 w-4" />
                  Cover Letter
                </CardTitle>
                <CardDescription>The cover letter written for this application.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {coverLettersLoading ? (
                  <div className="space-y-2 py-2">
                    <Skeleton className="h-4 w-2/3" />
                    <Skeleton className="h-24 w-full" />
                  </div>
                ) : coverLetterCount === 0 ? (
                  <div className="flex flex-col items-start gap-3">
                    <p className="text-sm text-muted-foreground">
                      No cover letter linked to this application yet.
                    </p>
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={() => setGenerateCoverLetterOpen(true)}
                    >
                      <Send className="mr-2 h-4 w-4" />
                      Generate a cover letter
                    </Button>
                  </div>
                ) : (
                  (coverLetters || []).map((cl) => (
                    <div key={cl.id} className="flex items-center justify-between gap-4">
                      <div className="min-w-0">
                        <div className="truncate font-medium">{cl.title}</div>
                        <div className="text-xs text-muted-foreground">
                          {cl.company_name ? `${cl.company_name} · ` : ""}
                          {cl.job_title || "Untitled"}
                        </div>
                      </div>
                      <Button type="button" variant="outline" size="sm" asChild>
                        <a href="/cover-letter-studio">Open</a>
                      </Button>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ---------------------------- JD Match --------------------------- */}
          <TabsContent value="jd-match" className="pt-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ClipboardList className="h-4 w-4" />
                  JD Match
                </CardTitle>
                <CardDescription>
                  Save the job description, then run Resume Match to see how your resume stacks up.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="job-description">Job Description</Label>
                  <Textarea
                    id="job-description"
                    value={jdValue}
                    onChange={(e) => setJdValue(e.target.value)}
                    placeholder="Paste the job description here so Resume Match and the Career Coach can use it..."
                    rows={6}
                    disabled={jdSaving}
                  />
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs text-muted-foreground">
                      {jdDirty
                        ? "Unsaved changes"
                        : hasJd
                          ? "Saved"
                          : "No job description saved yet"}
                    </p>
                    <Button
                      type="button"
                      size="sm"
                      onClick={() => saveJd()}
                      disabled={jdSaving || !jdDirty}
                    >
                      {jdSaving ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        "Save"
                      )}
                    </Button>
                  </div>
                </div>

                <Separator />

                {recheckError ? (
                  <Alert variant="destructive">
                    <AlertTitle>Re-check failed</AlertTitle>
                    <AlertDescription>
                      {recheckError?.response?.data?.message ||
                       recheckError?.response?.data?.detail ||
                       recheckError?.message ||
                       "Unable to re-check the match."}
                    </AlertDescription>
                  </Alert>
                ) : null}

                {matchJustRan && matchResult && (
                  <SuccessBanner onDismiss={() => setMatchJustRan(false)}>
                    Match complete — your resume&apos;s skill overlap with this job
                    description is shown below.
                  </SuccessBanner>
                )}

                {!hasJd && !jdDirty ? (
                  <div className="flex flex-col items-start gap-3">
                    <p className="text-sm text-muted-foreground">
                      Resume Match, the Career Coach, and Interview Preparation all need a saved Job
                      Description. Add one above, then run the match.
                    </p>
                  </div>
                ) : matchLoading ? (
                  <div className="space-y-2 py-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                  </div>
                ) : matchError ? (
                  <div className="flex flex-col items-start gap-3">
                    <p className="text-sm text-muted-foreground">
                      No match recorded for this application yet.
                    </p>
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={runMatch}
                      disabled={rechecking || jdSaving}
                    >
                      <RefreshCw className="mr-2 h-4 w-4" />
                      {rechecking ? "Matching..." : jdDirty ? "Save & Run Match" : "Run match"}
                    </Button>
                  </div>
                ) : matchResult ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Overall match score</span>
                      <div className="flex items-center gap-2">
                        {matchResult.used_ai ? <Badge variant="secondary">AI-enhanced</Badge> : null}
                        <ScoreTooltip description="Weighted blend of skill overlap (50%) and keyword match (30%) against the job description, plus a 20% experience bonus. 0 when the JD has nothing to match against.">
                          <span className="inline-flex cursor-help text-lg font-semibold">
                            {Math.round(matchResult.match_score)}%
                          </span>
                        </ScoreTooltip>
                      </div>
                    </div>

                    <Separator />

                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Missing skills</span>
                      <span className="text-sm font-medium">
                        {matchResult.missing_skills?.length ?? 0}
                      </span>
                    </div>

                    {matchResult.missing_skills?.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {matchResult.missing_skills.map((skill, idx) => (
                          <Badge key={idx} variant="outline">
                            {typeof skill === "string" ? skill : skill?.name || "Unknown"}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        No missing skills — strong coverage.
                      </p>
                    )}

                    <div className="pt-1">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={runMatch}
                        disabled={rechecking || jdSaving}
                      >
                        <RefreshCw className="mr-2 h-4 w-4" />
                        {rechecking
                          ? "Matching..."
                          : jdDirty
                            ? "Save & Re-check Match"
                            : "Re-check match"}
                      </Button>
                    </div>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          </TabsContent>

          {/* -------------------------- Communication ------------------------ */}
          <TabsContent value="communication" className="pt-4">
            <ApplicationCommunicationThread jobApplicationId={job?.id} />
          </TabsContent>

          {/* ---------------------------- Interview -------------------------- */}
          <TabsContent value="interview" className="pt-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquarePlus className="h-4 w-4" />
                  Real Interview Log
                </CardTitle>
                <CardDescription>
                  Retrospective notes on how your real interview for this application went. These
                  help the Career Coach tailor advice.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {realInterviewsLoading ? (
                  <div className="space-y-2 py-2">
                    <Skeleton className="h-4 w-40" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-2/3" />
                  </div>
                ) : interviewCount === 0 ? (
                  <div className="flex flex-col items-start gap-3">
                    <p className="text-sm text-muted-foreground">No real interviews logged yet.</p>
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={() => setLogInterviewOpen(true)}
                    >
                      <MessageSquarePlus className="mr-2 h-4 w-4" />
                      Log how this interview went
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {(realInterviews || []).map((ri) => (
                      <div
                        key={ri.id}
                        className="rounded-lg border border-border/60 bg-muted/30 p-3"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary">Real Interview</Badge>
                            <span className="text-xs text-muted-foreground">
                              {ri.started_at
                                ? new Date(ri.started_at).toLocaleDateString()
                                : ""}
                            </span>
                          </div>
                          <span className="text-sm font-semibold tabular-nums">
                            {Math.round(ri.self_rated_confidence ?? 0)}/100
                          </span>
                        </div>
                        {ri.how_it_went ? (
                          <p className="mt-2 whitespace-pre-line text-sm text-muted-foreground">
                            {ri.how_it_went}
                          </p>
                        ) : null}
                        {ri.questions_asked ? (
                          <div className="mt-2 text-xs text-muted-foreground">
                            <span className="font-medium text-foreground/80">Questions: </span>
                            {ri.questions_asked}
                          </div>
                        ) : null}
                      </div>
                    ))}
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setLogInterviewOpen(true)}
                    >
                      <MessageSquarePlus className="mr-2 h-4 w-4" />
                      Log another
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <details className="group mt-6">
          <summary className="flex cursor-pointer items-center gap-1 text-xs font-medium text-muted-foreground select-none hover:text-foreground">
            Job details
            <ChevronDown className="size-3.5 transition-transform group-open:rotate-180" />
          </summary>
          <div className="mt-3 space-y-2 rounded-lg border border-border/60 bg-muted/30 p-4 text-sm">
            <div className="flex justify-between gap-6">
              <div className="text-muted-foreground">Location</div>
              <div className="font-medium">{job?.location || "—"}</div>
            </div>
            <div className="flex justify-between gap-6">
              <div className="text-muted-foreground">Source</div>
              <div className="font-medium">{job?.source || "—"}</div>
            </div>
            <div className="flex justify-between gap-6">
              <div className="text-muted-foreground">Job URL</div>
              <div className="break-all font-medium">
                {job?.job_url ? (
                  <a href={job.job_url} target="_blank" rel="noreferrer" className="underline">
                    {job.job_url}
                  </a>
                ) : (
                  "—"
                )}
              </div>
            </div>
            <div className="flex justify-between gap-6">
              <div className="text-muted-foreground">Applied Date</div>
              <div className="font-medium">{formatDate(job?.applied_date)}</div>
            </div>
            <div className="flex justify-between gap-6">
              <div className="text-muted-foreground">Deadline</div>
              <div className="font-medium">{formatDate(job?.deadline)}</div>
            </div>
            {job?.notes ? (
              <div>
                <div className="text-muted-foreground">Notes</div>
                <div className="mt-1 whitespace-pre-wrap">{job.notes}</div>
              </div>
            ) : null}
          </div>
        </details>

        <div className="mt-5">
          <ApplicationActivityFeed jobApplicationId={job?.id} />
        </div>
      </div>

      <LinkResumeDialog
        open={linkResumeOpen}
        onOpenChange={setLinkResumeOpen}
        job={job}
        resumes={resumes}
        loading={resumesLoading}
        onLink={(resumeId) => {
          updateJob(
            { id: job.id, data: { resume_id: resumeId } },
            {
              onSuccess: () => {
                setLinkResumeOpen(false);
                queryClient.invalidateQueries({ queryKey: ["workspace", job.id] });
              },
            }
          );
        }}
      />

      <GenerateCoverLetterDialog
        open={generateCoverLetterOpen}
        onOpenChange={(next) => {
          setGenerateCoverLetterOpen(next);
          if (!next) {
            queryClient.invalidateQueries({ queryKey: ["coverLettersForJob", job?.id] });
            queryClient.invalidateQueries({ queryKey: ["workspace", job?.id] });
          }
        }}
        job={job}
        resumes={resumes}
        loading={resumesLoading}
      />

      <LogRealInterviewDialog
        open={logInterviewOpen}
        onOpenChange={setLogInterviewOpen}
        job={job}
        onLogged={() => {
          queryClient.invalidateQueries({ queryKey: ["realInterviewsForJob", job?.id] });
          queryClient.invalidateQueries({ queryKey: ["workspace", job?.id] });
        }}
      />
    </div>
  );
}
