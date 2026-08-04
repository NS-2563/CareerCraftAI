import { useMemo, useState } from "react";
import {
  Inbox,
  Send,
  Loader2,
  Sparkles,
  Mail,
  Calendar,
  Lock,
  RotateCcw,
  Mic,
  AlertTriangle,
  AlertCircle,
  Hourglass,
  Reply,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { StatusBadge, Skeleton, Timeline } from "@/components/ui/atoms";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { useThread } from "@/communication/hooks/useThread";
import { useLogInbound } from "@/communication/hooks/useLogInbound";
import { useGenerateMessage } from "@/communication/hooks/useGenerateMessage";
import { useConversationStatus, useSetConversationStatus } from "@/communication/hooks/useConversationStatus";
import MessageComposer from "@/communication/components/MessageComposer";
import { createMessage } from "@/communication/services/communicationApi";

import { useApplicationSessions } from "@/modules/jobTracker/hooks/useApplicationSessions";

import { useQueryClient } from "@tanstack/react-query";
import { formatTimeAgo } from "@/utils/dates";

const INTERVIEW_ACCENT = "var(--rose)";
const COMMUNICATION_ACCENT = "var(--teal)";

function formatTimestamp(d) {
  if (!d) return "";
  try {
    return new Date(d).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

function AiBadge() {
  return (
    <span className="inline-flex h-4 w-fit items-center rounded-full bg-violet-500/10 px-1.5 text-[10px] font-semibold text-violet-600 ring-1 ring-violet-500/30 dark:text-violet-400">
      <Sparkles className="mr-0.5 h-2.5 w-2.5" />
      AI
    </span>
  );
}

/**
 * Deterministic state chip for the per-application thread summary (the same
 * derivation the backend computes — never a client-invented value).
 */
function SummaryStateChip({ summary }) {
  if (!summary?.has_thread) return null;
  const state = summary.state;
  if (state === "response_overdue") {
    return (
      <Badge variant="soft" accent="#ef4444">
        <AlertTriangle className="mr-1 h-3 w-3" />
        Response overdue
        {summary.response_overdue_days != null ? ` · ${summary.response_overdue_days}d` : ""}
      </Badge>
    );
  }
  if (state === "needs_reply") {
    return (
      <Badge variant="soft" accent="#f59e0b">
        <AlertCircle className="mr-1 h-3 w-3" />
        Needs your reply
      </Badge>
    );
  }
  if (state === "waiting") {
    return (
      <Badge variant="soft" accent="#0ea5e9">
        <Hourglass className="mr-1 h-3 w-3" />
        Waiting for response
      </Badge>
    );
  }
  return null;
}

/**
 * Thread-summary chips: last reply, last recruiter email, and the derived
 * response state. Pure render of the backend-computed `thread_summary`.
 */
function ThreadSummaryChips({ summary }) {
  if (!summary?.has_thread) return null;
  return (
    <div className="flex flex-wrap items-center gap-2">
      {summary.last_reply?.created_at ? (
        <Badge variant="outline" className="text-xs">
          <Reply className="mr-1 h-3 w-3" />
          Last reply {formatTimeAgo(summary.last_reply.created_at)}
        </Badge>
      ) : null}
      {summary.last_recruiter_email?.created_at ? (
        <Badge variant="outline" className="text-xs">
          <Mail className="mr-1 h-3 w-3" />
          Last recruiter email {formatTimeAgo(summary.last_recruiter_email.created_at)}
        </Badge>
      ) : null}
      <SummaryStateChip summary={summary} />
    </div>
  );
}

function LogInboundDialog({ open, onOpenChange, jobApplicationId }) {
  const { mutate: logInbound, isPending, error } = useLogInbound();
  const [senderName, setSenderName] = useState("");
  const [senderEmail, setSenderEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [receivedDate, setReceivedDate] = useState("");

  const reset = () => {
    setSenderName("");
    setSenderEmail("");
    setSubject("");
    setBody("");
    setReceivedDate("");
  };

  const handleSubmit = () => {
    if (!body.trim()) return;
    logInbound(
      {
        related_job_application_id: jobApplicationId,
        sender_name: senderName || undefined,
        sender_email: senderEmail || undefined,
        subject: subject || undefined,
        body,
        received_at: receivedDate ? new Date(receivedDate).toISOString() : undefined,
      },
      {
        onSuccess: () => {
          reset();
          onOpenChange(false);
        },
      }
    );
  };

  const errMsg =
    error?.response?.data?.message ||
    error?.response?.data?.detail ||
    error?.message ||
    "";

  return (
    <Dialog open={open} onOpenChange={(next) => {
      onOpenChange(next);
      if (!next) reset();
    }}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Log an Email</DialogTitle>
          <DialogDescription>
            Paste a recruiter email received for this application. It will appear
            in this conversation thread.
          </DialogDescription>
        </DialogHeader>

        {errMsg ? (
          <Alert variant="destructive">
            <AlertTitle>Failed to log email</AlertTitle>
            <AlertDescription>{errMsg}</AlertDescription>
          </Alert>
        ) : null}

        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="sender_name">Sender Name (optional)</Label>
              <Input
                id="sender_name"
                value={senderName}
                onChange={(e) => setSenderName(e.target.value)}
                placeholder="e.g., Jane Smith"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="sender_email">Sender Email (optional)</Label>
              <Input
                id="sender_email"
                value={senderEmail}
                onChange={(e) => setSenderEmail(e.target.value)}
                placeholder="e.g., jane@acme.com"
                type="email"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="subject">Subject</Label>
              <Input
                id="subject"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Re: Application for Senior Engineer"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="received_at">Received Date (optional)</Label>
              <div className="relative">
                <Calendar className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="received_at"
                  type="datetime-local"
                  className="pl-8"
                  value={receivedDate}
                  onChange={(e) => setReceivedDate(e.target.value)}
                />
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="body">
              Email Body <span className="text-destructive">*</span>
            </Label>
            <Textarea
              id="body"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Paste the full email content here..."
              rows={8}
            />
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={isPending || !body.trim()}
          >
            {isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Mail className="mr-2 h-4 w-4" />
                Log Email
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ReplyComposerDialog({ message, jobApplicationId, onOpenChange }) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(true);

  const {
    mutate: generate,
    isPending: isGenerating,
    data: generatedMessage,
    error: generateErrorObj,
    isError: isGenerateError,
    reset: resetGenerate,
  } = useGenerateMessage();

  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  const generateError = isGenerateError
    ? (generateErrorObj?.response?.data?.message
       || generateErrorObj?.response?.data?.detail
       || generateErrorObj?.message
       || "Generation failed. Please try again.")
    : null;

  const is429 = isGenerateError && generateErrorObj?.response?.status === 429;

  const close = () => {
    resetGenerate();
    setSaveError(null);
    setOpen(false);
    onOpenChange(false);
  };

  const handleSave = async (data) => {
    setIsSaving(true);
    setSaveError(null);
    try {
      await createMessage(data);
      queryClient.invalidateQueries({ queryKey: ["communicationThread", jobApplicationId] });
      queryClient.invalidateQueries({ queryKey: ["communicationMessages"] });
      queryClient.invalidateQueries({ queryKey: ["workspace", jobApplicationId] });
      close();
    } catch (err) {
      setSaveError(err?.response?.data?.detail || err?.message || "Failed to save reply");
    } finally {
      setIsSaving(false);
    }
  };

  const senderName = message.sender_name || message.sender_email || "";

  return (
    <Dialog open={open} onOpenChange={(next) => {
      if (!next) close();
      else setOpen(next);
    }}>
      <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Generate AI Reply</DialogTitle>
          <DialogDescription>
            Draft a reply to {senderName || "the recruiter"} with full thread context.
          </DialogDescription>
        </DialogHeader>

        {saveError ? (
          <Alert variant="destructive">
            <AlertTitle>Failed to save</AlertTitle>
            <AlertDescription>{saveError}</AlertDescription>
          </Alert>
        ) : null}

        <MessageComposer
          messageType="recruiter_reply"
          onGenerate={generate}
          isGenerating={isGenerating}
          generatedMessage={generatedMessage}
          generateError={generateError}
          is429={is429}
          onSave={handleSave}
          isSaving={isSaving}
          initialJobId={jobApplicationId}
          initialInboundMessage={message.body}
          initialRecipientName={senderName}
        />
      </DialogContent>
    </Dialog>
  );
}

export default function ApplicationCommunicationThread({ jobApplicationId }) {
  const { data: messages, isLoading, isError, error } = useThread(jobApplicationId);
  const { data: sessions, isLoading: sessionsLoading } = useApplicationSessions(jobApplicationId);
  const { data: convStatus } = useConversationStatus(jobApplicationId);
  const { mutate: setStatus, isPending: isSettingStatus } = useSetConversationStatus();
  const [logOpen, setLogOpen] = useState(false);
  const [replyTarget, setReplyTarget] = useState(null);

  const thread = useMemo(
    () => (Array.isArray(messages) ? messages : []),
    [messages]
  );
  const appSessions = useMemo(
    () => (Array.isArray(sessions) ? sessions : []),
    [sessions]
  );

  const status = convStatus?.status ?? null;
  const statusSource = convStatus?.source ?? null;
  const isClosedByApplication = status === "closed" && statusSource === "application_status";

  // Deterministic thread summary is attached to every message of the thread by
  // the backend — they all carry the same per-application value.
  const summary = thread[0]?.thread_summary ?? null;

  const handleToggleClosed = () => {
    const next = status === "closed" ? null : "closed";
    setStatus({ jobApplicationId, status: next });
  };

  const handleItemClick = (item) => {
    if (item?.kind === "message" && item.message?.direction === "inbound") {
      setReplyTarget(item.message);
    }
  };

  // Merge messages + interview events into one chronological timeline
  // (oldest first, matching the conversation-thread order).
  const timelineItems = useMemo(() => {
    const items = [];

    for (const msg of thread) {
      const isInbound = msg.direction === "inbound";
      const author = isInbound
        ? (msg.sender_name || msg.sender_email || "Recruiter")
        : "You";
      items.push({
        id: `msg-${msg.id}`,
        kind: "message",
        message: msg,
        title: (
          <span className="inline-flex flex-wrap items-center gap-1.5">
            {author}
            {!isInbound && msg.generation_method === "ai_generated" ? <AiBadge /> : null}
          </span>
        ),
        subtitle: msg.subject || (isInbound ? "Recruiter email" : "Outbound message"),
        timestamp: formatTimeAgo(msg.created_at),
        accentColor: COMMUNICATION_ACCENT,
        linkable: isInbound,
        content: (
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5">
              <Badge variant="soft" className="text-[10px]">
                {isInbound ? <Inbox className="mr-1 h-3 w-3" /> : <Send className="mr-1 h-3 w-3" />}
                {isInbound ? "Inbound" : "Outbound"}
              </Badge>
              <span className="text-[10px] text-muted-foreground">
                {formatTimestamp(msg.created_at)}
              </span>
            </div>
            <div className="whitespace-pre-wrap rounded-lg border border-border/60 bg-muted/30 p-2.5 text-sm">
              {msg.body}
            </div>
          </div>
        ),
      });
    }

    for (const s of appSessions) {
      const isReal = s.session_type === "real_interview";
      const when = s.completed_at || s.started_at || s.created_at;
      items.push({
        id: `session-${s.id}`,
        kind: "interview",
        session: s,
        title: isReal
          ? "Real interview logged"
          : `Practice session${s.overall_score != null ? ` · ${s.overall_score}/100` : ""}`,
        subtitle: [
          s.job_title,
          s.company_name,
          s.self_rated_confidence != null ? `Confidence ${s.self_rated_confidence}` : null,
        ]
          .filter(Boolean)
          .join(" · "),
        timestamp: formatTimeAgo(when),
        accentColor: INTERVIEW_ACCENT,
        linkable: false,
        content: isReal ? (
          s.how_it_went ? (
            <div className="whitespace-pre-wrap rounded-lg border border-border/60 bg-muted/30 p-2.5 text-sm">
              {s.how_it_went}
            </div>
          ) : null
        ) : s.overall_score != null ? (
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Mic className="h-3.5 w-3.5" />
            Scored {s.overall_score}/100 on the practice session.
          </div>
        ) : null,
      });
    }

    items.sort((a, b) => {
      const timeOf = (item) => {
        if (item.kind === "message") {
          const d = item.message.created_at ? new Date(item.message.created_at).getTime() : 0;
          return Number.isNaN(d) ? 0 : d;
        }
        const when = item.session.completed_at || item.session.started_at || item.session.created_at;
        const d = when ? new Date(when).getTime() : 0;
        return Number.isNaN(d) ? 0 : d;
      };
      const diff = timeOf(a) - timeOf(b);
      if (diff !== 0) return diff;
      // Stable tiebreaker: id ascending, interviews after messages on the same time.
      return a.id.localeCompare(b.id);
    });

    return items;
  }, [thread, appSessions]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-medium">Conversation Thread</h3>
          <p className="text-xs text-muted-foreground">
            Emails, replies, and interview events for this application, in order.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {status ? (
            <StatusBadge status={status} />
          ) : null}
          {status && !isClosedByApplication ? (
            <Button
              type="button"
              variant={status === "closed" ? "outline" : "secondary"}
              size="sm"
              onClick={handleToggleClosed}
              disabled={isSettingStatus}
            >
              {status === "closed" ? (
                <>
                  <RotateCcw className="mr-1.5 h-3.5 w-3.5" />
                  Reopen
                </>
              ) : (
                <>
                  <Lock className="mr-1.5 h-3.5 w-3.5" />
                  Mark closed
                </>
              )}
            </Button>
          ) : null}
          <Button type="button" onClick={() => setLogOpen(true)}>
            <Mail className="mr-2 h-4 w-4" />
            Log an Email
          </Button>
        </div>
      </div>

      <ThreadSummaryChips summary={summary} />

      {isLoading || sessionsLoading ? (
        <div className="space-y-3 rounded-xl border p-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex gap-3">
              <Skeleton circle className="size-7" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-3 w-1/3" />
                <Skeleton className="h-4 w-full" />
              </div>
            </div>
          ))}
        </div>
      ) : isError ? (
        <Alert variant="destructive">
          <AlertTitle>Failed to load thread</AlertTitle>
          <AlertDescription>
            {error?.response?.data?.message ||
             error?.response?.data?.detail ||
             error?.message ||
             "Unable to load the conversation thread."}
          </AlertDescription>
        </Alert>
      ) : timelineItems.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12 text-center">
          <Mail className="mb-3 h-8 w-8 text-muted-foreground" />
          <h4 className="font-medium">No activity yet</h4>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Log the first recruiter email, draft a message from the
            Communication Hub, or log an interview to start this timeline.
          </p>
          <Button className="mt-4" variant="secondary" onClick={() => setLogOpen(true)}>
            <Mail className="mr-2 h-4 w-4" />
            Log an Email
          </Button>
        </div>
      ) : (
        <div className="max-h-[480px] overflow-y-auto rounded-xl border p-4">
          <Timeline
            items={timelineItems}
            iconFor={(item) => {
              if (item.kind === "message") {
                return item.message.direction === "inbound" ? Inbox : Send;
              }
              return Mic;
            }}
            onItemClick={handleItemClick}
          />
        </div>
      )}

      {thread.length > 0 && (
        <p className="text-xs text-muted-foreground">
          {thread.length} message{thread.length === 1 ? "" : "s"} ·{" "}
          {appSessions.length} interview event{appSessions.length === 1 ? "" : "s"}
        </p>
      )}

      <LogInboundDialog
        open={logOpen}
        onOpenChange={setLogOpen}
        jobApplicationId={jobApplicationId}
      />

      {replyTarget && (
        <ReplyComposerDialog
          message={replyTarget}
          jobApplicationId={jobApplicationId}
          onOpenChange={() => setReplyTarget(null)}
        />
      )}
    </div>
  );
}
