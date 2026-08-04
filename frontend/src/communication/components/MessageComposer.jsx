import { useState, useCallback } from "react";
import { Copy, Mail, Loader2, Sparkles, AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useJobs } from "@/modules/jobTracker/hooks/useJobs";

const TONES = ["professional", "friendly", "executive", "creative"];
const REPLY_INTENTS = [
  { value: "accept_interest", label: "Accept & Express Interest", description: "I'm interested and want to move forward" },
  { value: "decline_politely", label: "Politely Decline", description: "Not interested right now, but keep the door open" },
  { value: "negotiate_timing", label: "Negotiate Timing", description: "Interested but need to adjust timing" },
  { value: "ask_clarifying_questions", label: "Ask Clarifying Questions", description: "Need more info before deciding" },
];

export default function MessageComposer({
  messageType,
  onGenerate,
  isGenerating,
  generatedMessage,
  generateError,
  is429,
  onSave,
  isSaving,
  initialJobId,
  initialInboundMessage,
  initialRecipientName,
  initialRecipientCompany,
}) {
  const { data: jobsData } = useJobs();
  const jobs = Array.isArray(jobsData) ? jobsData : [];

  const isLinkedInNote = messageType === "linkedin_note";
  const isRecruiterReply = messageType === "recruiter_reply";

  const [recipientName, setRecipientName] = useState(initialRecipientName || "");
  const [recipientRole, setRecipientRole] = useState("");
  const [recipientCompany, setRecipientCompany] = useState(initialRecipientCompany || "");
  const [tone, setTone] = useState("professional");
  const [customContext, setCustomContext] = useState("");
  const [selectedJobId, setSelectedJobId] = useState(initialJobId || null);

  const [inboundMessage, setInboundMessage] = useState(initialInboundMessage || "");
  const [replyIntent, setReplyIntent] = useState("");

  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

  const [prevInitialJobId, setPrevInitialJobId] = useState(initialJobId);

  if (initialJobId !== prevInitialJobId) {
    setPrevInitialJobId(initialJobId);
    if (initialJobId) {
      setSelectedJobId(initialJobId);
    }
  }

  const [prevInitialInbound, setPrevInitialInbound] = useState(initialInboundMessage);

  if (initialInboundMessage !== prevInitialInbound) {
    setPrevInitialInbound(initialInboundMessage);
    if (initialInboundMessage) {
      setInboundMessage(initialInboundMessage);
    }
  }

  const [prevInitialRecipient, setPrevInitialRecipient] = useState(initialRecipientName);

  if (initialRecipientName !== prevInitialRecipient) {
    setPrevInitialRecipient(initialRecipientName);
    if (initialRecipientName) {
      setRecipientName(initialRecipientName);
    }
  }

  const [prevInitialCompany, setPrevInitialCompany] = useState(initialRecipientCompany);

  if (initialRecipientCompany !== prevInitialCompany) {
    setPrevInitialCompany(initialRecipientCompany);
    if (initialRecipientCompany) {
      setRecipientCompany(initialRecipientCompany);
    }
  }

  const [prevJobKey, setPrevJobKey] = useState("");

  if (`${selectedJobId ?? ""}:${jobs.length}` !== prevJobKey) {
    setPrevJobKey(`${selectedJobId ?? ""}:${jobs.length}`);
    if (selectedJobId) {
      const job = jobs.find((j) => j.id === Number(selectedJobId));
      if (job) {
        if (!recipientCompany) setRecipientCompany(job.company || "");
        if (!recipientRole) setRecipientRole(job.job_title || "");
      }
    }
  }

  const handleGenerate = useCallback(() => {
    const payload = {
      message_type: messageType,
      tone,
      recipient_name: recipientName || undefined,
      recipient_role: recipientRole || undefined,
      recipient_company: recipientCompany || undefined,
      custom_context: customContext || undefined,
    };
    if (isRecruiterReply) {
      payload.inbound_message = inboundMessage;
      payload.reply_intent = replyIntent;
    }
    if (selectedJobId) {
      payload.related_job_application_id = Number(selectedJobId);
    }
    onGenerate(payload);
  }, [messageType, tone, recipientName, recipientRole, recipientCompany, customContext, selectedJobId, inboundMessage, replyIntent, isRecruiterReply, onGenerate]);

  const handleCopyBody = useCallback(() => {
    const text = isLinkedInNote ? body : (subject ? `Subject: ${subject}\n\n${body}` : body);
    navigator.clipboard.writeText(text);
  }, [subject, body, isLinkedInNote]);

  const handleMailTo = useCallback(() => {
    if (isLinkedInNote) return;
    const mailtoLink = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.open(mailtoLink, "_blank");
  }, [subject, body, isLinkedInNote]);

  const handleSave = useCallback(() => {
    const payload = {
      message_type: messageType,
      tone,
      recipient_name: recipientName || undefined,
      recipient_role: recipientRole || undefined,
      recipient_company: recipientCompany || undefined,
      body,
    };
    if (!isLinkedInNote) {
      payload.subject = subject || undefined;
    }
    if (selectedJobId) {
      payload.related_job_application_id = Number(selectedJobId);
    }
    onSave(payload);
  }, [messageType, tone, recipientName, recipientRole, recipientCompany, subject, body, selectedJobId, isLinkedInNote, onSave]);

  const LINKEDIN_MAX_CHARS = 300;
  const linkedinCharCount = body.length;
  const linkedinOverLimit = linkedinCharCount > LINKEDIN_MAX_CHARS;

  const typeLabel =
    messageType === "cold_email" ? "Cold Email"
    : messageType === "follow_up" ? "Follow-Up"
    : messageType === "thank_you" ? "Thank-You Note"
    : messageType === "linkedin_note" ? "LinkedIn Note"
    : messageType === "recruiter_reply" ? "Reply to a Recruiter"
    : "Referral Request";

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{typeLabel} — Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="linked_job">Link to Job Application (optional)</Label>
            <select
              id="linked_job"
              className="h-9 w-full min-w-0 rounded-md border border-input bg-transparent px-2.5 shadow-xs outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50"
              value={selectedJobId || ""}
              onChange={(e) => setSelectedJobId(e.target.value ? Number(e.target.value) : null)}
              disabled={isGenerating}
            >
              <option value="">None</option>
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.company} — {job.job_title}
                </option>
              ))}
            </select>
          </div>

          {isRecruiterReply && (
            <>
              <div className="space-y-2">
                <Label htmlFor="inbound_message">
                  Recruiter's Message <span className="text-destructive">*</span>
                </Label>
                <Textarea
                  id="inbound_message"
                  value={inboundMessage}
                  onChange={(e) => setInboundMessage(e.target.value)}
                  placeholder="Paste the recruiter's email or LinkedIn message here..."
                  rows={6}
                  disabled={isGenerating}
                />
              </div>

              <div className="space-y-2">
                <Label>
                  Your Reply Intent <span className="text-destructive">*</span>
                </Label>
                <div className="grid gap-2 sm:grid-cols-2">
                  {REPLY_INTENTS.map((intent) => (
                    <button
                      key={intent.value}
                      type="button"
                      onClick={() => setReplyIntent(intent.value)}
                      disabled={isGenerating}
                      className={`text-left p-3 rounded-md border transition-all ${
                        replyIntent === intent.value
                          ? "border-primary ring-2 ring-primary/20 bg-primary/5"
                          : "border-input hover:border-muted-foreground"
                      }`}
                    >
                      <div className="text-sm font-medium">{intent.label}</div>
                      <div className="text-xs text-muted-foreground mt-0.5">{intent.description}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="space-y-2">
                  <Label htmlFor="recipient_name">Recruiter Name (optional)</Label>
                  <Input
                    id="recipient_name"
                    value={recipientName}
                    onChange={(e) => setRecipientName(e.target.value)}
                    placeholder="e.g., Jane Smith"
                    disabled={isGenerating}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="recipient_role">Role (optional)</Label>
                  <Input
                    id="recipient_role"
                    value={recipientRole}
                    onChange={(e) => setRecipientRole(e.target.value)}
                    placeholder="e.g., Technical Recruiter"
                    disabled={isGenerating}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="recipient_company">Company (optional)</Label>
                  <Input
                    id="recipient_company"
                    value={recipientCompany}
                    onChange={(e) => setRecipientCompany(e.target.value)}
                    placeholder="e.g., Acme Corp"
                    disabled={isGenerating}
                  />
                </div>
              </div>
            </>
          )}

          {!isRecruiterReply && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="recipient_name">Recipient Name</Label>
                <Input
                  id="recipient_name"
                  value={recipientName}
                  onChange={(e) => setRecipientName(e.target.value)}
                  placeholder="e.g., Jane Smith"
                  disabled={isGenerating}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="recipient_role">Recipient Role</Label>
                <Input
                  id="recipient_role"
                  value={recipientRole}
                  onChange={(e) => setRecipientRole(e.target.value)}
                  placeholder="e.g., Hiring Manager"
                  disabled={isGenerating}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="recipient_company">Company</Label>
                <Input
                  id="recipient_company"
                  value={recipientCompany}
                  onChange={(e) => setRecipientCompany(e.target.value)}
                  placeholder="e.g., Acme Corp"
                  disabled={isGenerating}
                />
              </div>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="tone">Tone</Label>
            <select
              id="tone"
              className="h-9 w-full min-w-0 rounded-md border border-input bg-transparent px-2.5 shadow-xs outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50"
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              disabled={isGenerating}
            >
              {TONES.map((t) => (
                <option key={t} value={t}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="custom_context">Additional Context (optional)</Label>
            <Textarea
              id="custom_context"
              value={customContext}
              onChange={(e) => setCustomContext(e.target.value)}
              placeholder={
                messageType === "thank_you"
                  ? "Something discussed in the interview..."
                  : isRecruiterReply
                  ? "Any additional details about your situation..."
                  : "Any specific details to include..."
              }
              rows={3}
              disabled={isGenerating}
            />
          </div>

          {generateError && (
            <div className="flex items-start gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>
                {is429
                  ? "Too many AI generation requests. Please wait a moment and try again."
                  : generateError}
              </span>
            </div>
          )}

          <Button
            type="button"
            onClick={handleGenerate}
            disabled={isGenerating || (isRecruiterReply && (!inboundMessage.trim() || !replyIntent))}
            className="w-full"
          >
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Generate with AI
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {generatedMessage && (
        <Card>
          <CardHeader>
            <CardTitle>Generated Message</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!isLinkedInNote && (
              <div className="space-y-2">
                <Label htmlFor="subject">Subject</Label>
                <Input
                  id="subject"
                  value={subject || generatedMessage.subject || ""}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="Email subject..."
                />
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="body">
                Body
                {isLinkedInNote && (
                  <span className={`ml-2 text-xs ${linkedinOverLimit ? "text-destructive font-semibold" : "text-muted-foreground"}`}>
                    ({linkedinCharCount}/{LINKEDIN_MAX_CHARS} chars
                    {linkedinOverLimit ? ` — ${linkedinCharCount - LINKEDIN_MAX_CHARS} over limit` : ""})
                  </span>
                )}
              </Label>
              <Textarea
                id="body"
                value={body || generatedMessage.body || ""}
                onChange={(e) => setBody(e.target.value)}
                rows={isLinkedInNote ? 4 : 12}
                className="font-mono text-sm"
              />
              {isLinkedInNote && linkedinOverLimit && (
                <div className="flex items-center gap-1 text-xs text-destructive">
                  <AlertTriangle className="h-3 w-3" />
                  LinkedIn connection notes have a ~300 character limit. Please shorten your message.
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleCopyBody}
              >
                <Copy className="mr-2 h-4 w-4" />
                Copy to Clipboard
              </Button>
              {!isLinkedInNote && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleMailTo}
                >
                  <Mail className="mr-2 h-4 w-4" />
                  Open in Mail Client
                </Button>
              )}
              <Button
                type="button"
                onClick={handleSave}
                disabled={isSaving}
                className="ml-auto"
              >
                {isSaving ? "Saving..." : "Save Message"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
