import { useState, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Plus,
  Mail,
  Send,
  Heart,
  MessageSquare,
  UserPlus,
  Copy,
  Archive,
  EllipsisVertical,
  FileText,
  MessagesSquare,
  Reply,
  Sparkles,
  AlertTriangle,
  AlertCircle,
  Hourglass,
} from "lucide-react";

import {
  Card,
  CardHeader,
  CardTitle,
  CardAction,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { StatusBadge, Skeleton } from "@/components/ui/atoms";

import MessageTypeSelector from "../components/MessageTypeSelector";
import MessageComposer from "../components/MessageComposer";

import { useMessages } from "../hooks/useMessages";
import { useGenerateMessage } from "../hooks/useGenerateMessage";
import { useDeleteMessage } from "../hooks/useDeleteMessage";
import {
  createMessage,
  archiveMessage,
  restoreMessage,
  duplicateMessage,
  renameMessage,
} from "../services/communicationApi";

import { useQueryClient } from "@tanstack/react-query";
import { formatTimeAgo } from "@/utils/dates";

const TYPE_META = {
  cold_email: { label: "Cold Email", icon: Mail, color: "bg-blue-50 text-blue-700 border-blue-200" },
  follow_up: { label: "Follow-Up", icon: Send, color: "bg-amber-50 text-amber-700 border-amber-200" },
  thank_you: { label: "Thank-You", icon: Heart, color: "bg-green-50 text-green-700 border-green-200" },
  linkedin_note: { label: "LinkedIn Note", icon: MessageSquare, color: "bg-sky-50 text-sky-700 border-sky-200" },
  referral_request: { label: "Referral Request", icon: UserPlus, color: "bg-purple-50 text-purple-700 border-purple-200" },
  recruiter_reply: { label: "Recruiter Reply", icon: Reply, color: "bg-indigo-50 text-indigo-700 border-indigo-200" },
  recruiter_email: { label: "Recruiter Email", icon: Mail, color: "bg-teal-50 text-teal-700 border-teal-200" },
};

const FILTER_OPTIONS = [
  { value: null, label: "All" },
  { value: "cold_email", label: "Cold Email" },
  { value: "follow_up", label: "Follow-Up" },
  { value: "thank_you", label: "Thank-You" },
  { value: "linkedin_note", label: "LinkedIn" },
  { value: "referral_request", label: "Referral" },
  { value: "recruiter_reply", label: "Recruiter Reply" },
  { value: "recruiter_email", label: "Recruiter Email" },
];

const CONVERSATION_FILTER_OPTIONS = [
  { value: null, label: "All conversations" },
  { value: "needs_reply", label: "Needs Reply" },
  { value: "waiting", label: "Waiting" },
  { value: "closed", label: "Closed" },
];

// Rank for "Needs attention first" sort: conversations that need action float up.
const ATTENTION_RANK = { needs_reply: 0, waiting: 1, closed: 2 };

function formatDate(d) {
  if (!d) return "";
  try {
    return new Date(d).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return "";
  }
}

function AiBadge() {
  return (
    <Badge variant="soft" accent="#8b5cf6" className="text-[10px]">
      <Sparkles className="mr-1 h-3 w-3" />
      AI
    </Badge>
  );
}

/**
 * Compact per-application thread-summary chips for the hub card. Renders the
 * deterministic summary computed by the backend — never a client-invented value.
 */
function ThreadSummaryChips({ summary }) {
  if (!summary?.has_thread) return null;
  const state = summary.state;
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {summary.last_reply?.created_at ? (
        <Badge variant="outline" className="text-[10px]">
          <Reply className="mr-1 h-3 w-3" />
          Last reply {formatTimeAgo(summary.last_reply.created_at)}
        </Badge>
      ) : null}
      {summary.last_recruiter_email?.created_at ? (
        <Badge variant="outline" className="text-[10px]">
          <Mail className="mr-1 h-3 w-3" />
          Recruiter {formatTimeAgo(summary.last_recruiter_email.created_at)}
        </Badge>
      ) : null}
      {state === "response_overdue" ? (
        <Badge variant="soft" accent="#ef4444" className="text-[10px]">
          <AlertTriangle className="mr-1 h-3 w-3" />
          Response overdue
          {summary.response_overdue_days != null ? ` · ${summary.response_overdue_days}d` : ""}
        </Badge>
      ) : null}
      {state === "needs_reply" ? (
        <Badge variant="soft" accent="#f59e0b" className="text-[10px]">
          <AlertCircle className="mr-1 h-3 w-3" />
          Needs your reply
        </Badge>
      ) : null}
      {state === "waiting" ? (
        <Badge variant="soft" accent="#0ea5e9" className="text-[10px]">
          <Hourglass className="mr-1 h-3 w-3" />
          Waiting for response
        </Badge>
      ) : null}
    </div>
  );
}

function MessageCard({ message, onAction }) {
  const meta = TYPE_META[message.message_type] || TYPE_META.cold_email;
  const Icon = meta.icon;
  const navigate = useNavigate();

  const handleCopy = () => {
    const text = message.subject
      ? `Subject: ${message.subject}\n\n${message.body}`
      : message.body;
    navigator.clipboard.writeText(text);
  };

  return (
    <Card
      className={
        message.is_archived
          ? "border-dashed border-gray-300 bg-gray-50/40"
          : "hover:shadow-md transition-shadow"
      }
    >
      <CardHeader>
        <div className="flex items-center gap-2">
          <CardTitle className="truncate text-sm">
            {message.subject || `${meta.label} — ${message.recipient_name || "No Subject"}`}
          </CardTitle>
          <CardAction>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon-sm" aria-label="Message actions">
                  <EllipsisVertical className="size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-40">
                {message.related_job_application_id ? (
                  <DropdownMenuItem
                    onClick={() =>
                      navigate(`/jobs?viewJob=${message.related_job_application_id}&tab=communication`)
                    }
                  >
                    <MessagesSquare className="mr-2 h-4 w-4" />
                    View Thread
                  </DropdownMenuItem>
                ) : null}
                <DropdownMenuItem onClick={() => onAction("duplicate", message)}>
                  Duplicate
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onAction("rename", message)}>
                  Rename
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onAction("history", message)}>
                  History
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                {message.is_archived ? (
                  <DropdownMenuItem onClick={() => onAction("restore", message)}>
                    Restore
                  </DropdownMenuItem>
                ) : (
                  <DropdownMenuItem onClick={() => onAction("archive", message)}>
                    Archive
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive focus:bg-destructive/10"
                  onClick={() => onAction("delete", message)}
                >
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </CardAction>
        </div>
        <CardDescription className="flex items-center gap-2">
          <Badge variant="outline" className={meta.color}>
            <Icon className="mr-1 h-3 w-3" />
            {meta.label}
          </Badge>
          <Badge variant="secondary" className="text-xs">
            v{message.version}
          </Badge>
          {message.conversation_status ? (
            <StatusBadge status={message.conversation_status} />
          ) : null}
          {message.direction !== "inbound" && message.generation_method === "ai_generated" ? (
            <AiBadge />
          ) : null}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-2">
        {message.recipient_name && (
          <div className="text-xs text-muted-foreground">
            To: {message.recipient_name}
            {message.recipient_role ? ` (${message.recipient_role})` : ""}
            {message.recipient_company ? ` @ ${message.recipient_company}` : ""}
          </div>
        )}
        <div className="line-clamp-3 text-sm text-muted-foreground">
          {message.body}
        </div>
        {message.thread_summary?.has_thread ? (
          <ThreadSummaryChips summary={message.thread_summary} />
        ) : null}
      </CardContent>

      <CardFooter className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">
          {formatDate(message.updated_at || message.created_at)}
        </span>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon-sm" onClick={handleCopy} title="Copy to clipboard">
            <Copy className="h-3.5 w-3.5" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}

function NewMessageDialog({ open, onOpenChange, initialJobId, initialType }) {
  const [step, setStep] = useState(initialType ? "compose" : "select");
  const [messageType, setMessageType] = useState(initialType || null);
  const queryClient = useQueryClient();

  const {
    mutate: generate,
    isPending: isGenerating,
    data: generatedMessage,
    error: generateErrorObj,
    isError: isGenerateError,
    reset: resetGenerate,
  } = useGenerateMessage();

  const generateError = isGenerateError
    ? (generateErrorObj?.response?.data?.message
       || generateErrorObj?.response?.data?.detail
       || generateErrorObj?.message
       || "Generation failed. Please try again.")
    : null;

  const is429 = isGenerateError && generateErrorObj?.response?.status === 429;

  const [saveError, setSaveError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  const handleTypeSelect = (type) => {
    setMessageType(type);
    setStep("compose");
  };

  const handleBack = () => {
    setStep("select");
    setMessageType(null);
    resetGenerate();
    setSaveError(null);
  };

  const handleGenerate = (data) => {
    setSaveError(null);
    generate(data);
  };

  const handleSave = async (data) => {
    setIsSaving(true);
    setSaveError(null);
    try {
      await createMessage(data);
      queryClient.invalidateQueries({ queryKey: ["communicationMessages"] });
      handleClose();
    } catch (err) {
      setSaveError(err?.response?.data?.detail || err?.message || "Failed to save message");
    } finally {
      setIsSaving(false);
    }
  };

  const handleClose = () => {
    setStep(initialType ? "compose" : "select");
    setMessageType(initialType || null);
    resetGenerate();
    setSaveError(null);
    onOpenChange(false);
  };

  const typeTitle = messageType
    ? messageType === "linkedin_note"
      ? "LinkedIn Note"
      : messageType === "referral_request"
      ? "Referral Request"
      : messageType.replace("_", "-")
    : "";

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {step === "select" ? "New Message" : `New ${typeTitle}`}
          </DialogTitle>
          <DialogDescription>
            {step === "select"
              ? "Choose the type of message you want to create."
              : "Fill in the details and generate with AI."}
          </DialogDescription>
        </DialogHeader>

        {saveError && (
          <Alert variant="destructive">
            <AlertTitle>Failed to save</AlertTitle>
            <AlertDescription>{saveError}</AlertDescription>
          </Alert>
        )}

        {step === "select" ? (
          <MessageTypeSelector onSelect={handleTypeSelect} />
        ) : (
          <MessageComposer
            messageType={messageType}
            onGenerate={handleGenerate}
            isGenerating={isGenerating}
            generatedMessage={generatedMessage}
            generateError={generateError}
            is429={is429}
            onSave={handleSave}
            isSaving={isSaving}
            initialJobId={initialJobId}
          />
        )}

        {step === "compose" && (
          <DialogFooter>
            <Button variant="ghost" onClick={handleBack} disabled={isGenerating}>
              Back to type selection
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function CommunicationHub() {
  const [searchParams, setSearchParams] = useSearchParams();
  const jobIdParam = searchParams.get("jobId");
  const typeParam = searchParams.get("type");

  const initialJobId = jobIdParam ? Number(jobIdParam) : null;
  const initialType = typeParam || null;

  const [newDialogOpen, setNewDialogOpen] = useState(!!initialJobId);
  const [filterType, setFilterType] = useState(null);
  const [showArchived, setShowArchived] = useState(false);
  const [convFilter, setConvFilter] = useState(null);
  const [sortAttention, setSortAttention] = useState(false);
  const queryClient = useQueryClient();

  const params = {};
  if (filterType) params.message_type = filterType;
  params.archived = showArchived;

  const { data: messages, isLoading, isError, error } = useMessages(params);
  const { mutate: deleteMsg, isPending: isDeleting } = useDeleteMessage();

  const [confirmDelete, setConfirmDelete] = useState(null);
  const [renameTarget, setRenameTarget] = useState(null);
  const [renameValue, setRenameValue] = useState("");

  const handleAction = useCallback(
    (action, message) => {
      if (action === "delete") {
        setConfirmDelete(message);
      } else if (action === "rename") {
        setRenameTarget(message);
        setRenameValue(message.subject || "");
      } else if (action === "archive") {
        archiveMessage(message.id).then(() => {
          queryClient.invalidateQueries({ queryKey: ["communicationMessages"] });
        });
      } else if (action === "restore") {
        restoreMessage(message.id).then(() => {
          queryClient.invalidateQueries({ queryKey: ["communicationMessages"] });
        });
      } else if (action === "duplicate") {
        duplicateMessage(message.id, { title: `Copy of ${message.subject || "Message"}` }).then(
          () => {
            queryClient.invalidateQueries({ queryKey: ["communicationMessages"] });
          }
        );
      }
    },
    [queryClient]
  );

  const handleConfirmDelete = () => {
    if (confirmDelete) {
      deleteMsg(confirmDelete.id, {
        onSuccess: () => setConfirmDelete(null),
      });
    }
  };

  const handleRename = async () => {
    if (renameTarget && renameValue.trim()) {
      try {
        await renameMessage(renameTarget.id, { title: renameValue.trim() });
        queryClient.invalidateQueries({ queryKey: ["communicationMessages"] });
        setRenameTarget(null);
      } catch {
        // handled by error state
      }
    }
  };

  const handleNewDialogOpenChange = (open) => {
    setNewDialogOpen(open);
    if (!open) {
      if (searchParams.has("jobId") || searchParams.has("type")) {
        setSearchParams({});
      }
    }
  };

  const messageList = Array.isArray(messages) ? messages : [];

  let visibleMessages = messageList;
  if (convFilter) {
    visibleMessages = visibleMessages.filter(
      (m) => m.conversation_status === convFilter
    );
  }
  if (sortAttention) {
    visibleMessages = [...visibleMessages].sort((a, b) => {
      const rankA = ATTENTION_RANK[a.conversation_status] ?? 3;
      const rankB = ATTENTION_RANK[b.conversation_status] ?? 3;
      if (rankA !== rankB) return rankA - rankB;
      return new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at);
    });
  }

  const Header = (
    <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-xl font-semibold leading-tight">Communication</h1>
        <p className="text-sm text-muted-foreground">
          Cold emails, follow-ups, LinkedIn notes, and more
        </p>
      </div>
      <Button type="button" onClick={() => setNewDialogOpen(true)}>
        <Plus className="mr-2 h-4 w-4" />
        New Message
      </Button>
    </header>
  );

  const Filters = (
    <div className="flex flex-wrap items-center gap-2">
      <div className="flex items-center gap-1 flex-wrap">
        {FILTER_OPTIONS.map((opt) => (
          <Button
            key={opt.value ?? "all"}
            variant={filterType === opt.value ? "default" : "outline"}
            size="sm"
            onClick={() => setFilterType(opt.value)}
          >
            {opt.label}
          </Button>
        ))}
      </div>
      <div className="ml-auto">
        <Button
          variant={showArchived ? "default" : "outline"}
          size="sm"
          onClick={() => setShowArchived((p) => !p)}
        >
          <Archive className="mr-1 h-4 w-4" />
          {showArchived ? "Archived" : "Active"}
        </Button>
      </div>
    </div>
  );

  const ConversationFilters = (
    <div className="flex flex-wrap items-center gap-2 border-t border-border/60 pt-3">
      <span className="text-xs font-medium text-muted-foreground">Conversation:</span>
      <div className="flex flex-wrap items-center gap-1">
        {CONVERSATION_FILTER_OPTIONS.map((opt) => (
          <Button
            key={opt.value ?? "all-conv"}
            variant={convFilter === opt.value ? "default" : "outline"}
            size="sm"
            onClick={() => setConvFilter(opt.value)}
          >
            {opt.label}
          </Button>
        ))}
      </div>
      <div className="ml-auto">
        <Button
          variant={sortAttention ? "default" : "outline"}
          size="sm"
          onClick={() => setSortAttention((p) => !p)}
        >
          <MessagesSquare className="mr-1 h-4 w-4" />
          Needs attention first
        </Button>
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Header}
        {Filters}
        {ConversationFilters}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Skeleton circle className="size-8" />
                  <Skeleton className="h-4 w-24" />
                </div>
                <Skeleton className="h-5 w-16" />
              </div>
              <Skeleton className="mt-3 h-4 w-full" />
              <Skeleton className="mt-2 h-4 w-3/4" />
              <div className="mt-4 flex items-center justify-between">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-6 w-6" />
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-4">
        {Header}
        {Filters}
        {ConversationFilters}
        <Alert variant="destructive">
          <AlertTitle>Failed to load messages</AlertTitle>
          <AlertDescription>
            {error?.response?.data?.detail || error?.message || "Unable to load messages."}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {Header}
      {Filters}
      {ConversationFilters}

      {visibleMessages.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-center">
          <FileText className="mb-4 h-12 w-12 text-muted-foreground" />
          <h2 className="text-xl font-semibold">
            {convFilter
              ? `No conversations ${convFilter.replace("_", " ")}`
              : showArchived
              ? "No archived messages"
              : "No messages yet"}
          </h2>
          <p className="mt-2 text-muted-foreground max-w-md">
            {convFilter
              ? "Try a different conversation filter, or create a new message."
              : showArchived
              ? "Archive messages to see them here."
              : "Create your first cold email, follow-up, or LinkedIn note."}
          </p>
          {!showArchived && (
            <Button className="mt-6" onClick={() => setNewDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              New Message
            </Button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {visibleMessages.map((msg) => (
            <MessageCard
              key={msg.id}
              message={msg}
              onAction={handleAction}
            />
          ))}
        </div>
      )}

      <NewMessageDialog
        open={newDialogOpen}
        onOpenChange={handleNewDialogOpenChange}
        initialJobId={initialJobId}
        initialType={initialType}
      />

      <Dialog open={!!confirmDelete} onOpenChange={() => setConfirmDelete(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Delete Message</DialogTitle>
            <DialogDescription>
              This action cannot be undone. Are you sure you want to delete this message?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setConfirmDelete(null)} disabled={isDeleting}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete} disabled={isDeleting}>
              {isDeleting ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!renameTarget} onOpenChange={() => setRenameTarget(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Rename Message</DialogTitle>
            <DialogDescription>Set a new subject for this message.</DialogDescription>
          </DialogHeader>
          <Input
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            placeholder="New subject..."
            autoFocus
          />
          <DialogFooter>
            <Button variant="secondary" onClick={() => setRenameTarget(null)}>
              Cancel
            </Button>
            <Button onClick={handleRename}>Rename</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
