import { useState } from "react";
import { Loader2, MessageSquarePlus } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import { createRealInterview } from "@/modules/interview/services/interviewSessionApi";

export default function LogRealInterviewDialog({ open, onOpenChange, job, onLogged }) {
  const [howItWent, setHowItWent] = useState("");
  const [confidence, setConfidence] = useState(50);
  const [questionsAsked, setQuestionsAsked] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);

  async function handleSave() {
    setError(null);
    if (!howItWent.trim()) {
      setError("Tell us how the interview went.");
      return;
    }
    setIsSaving(true);
    try {
      const result = await createRealInterview({
        job_application_id: job?.id,
        how_it_went: howItWent.trim(),
        self_rated_confidence: confidence,
        questions_asked: questionsAsked.trim() || null,
      });
      if (!result?.success) {
        setError(result?.error || "Failed to save the interview log.");
        return;
      }
      setHowItWent("");
      setConfidence(50);
      setQuestionsAsked("");
      onLogged?.();
      onOpenChange(false);
    } catch (err) {
      setError(err?.message || "Failed to save the interview log.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Log how this interview went</DialogTitle>
          <DialogDescription>
            A quick retrospective for your {job?.job_title || "interview"} at{" "}
            {job?.company || "this application"}. This is a lightweight log, not
            a full practice session.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {error ? (
            <Alert variant="destructive">
              <AlertTitle>Could not save</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}

          <div className="space-y-2">
            <Label htmlFor="ri-how">How did it go?</Label>
            <Textarea
              id="ri-how"
              value={howItWent}
              onChange={(e) => setHowItWent(e.target.value)}
              placeholder="Overall impression, what went well, what felt shaky..."
              rows={4}
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="ri-confidence">Self-rated confidence</Label>
              <span className="text-sm font-semibold tabular-nums">{confidence}/100</span>
            </div>
            <input
              id="ri-confidence"
              type="range"
              min={0}
              max={100}
              step={5}
              value={confidence}
              onChange={(e) => setConfidence(Number(e.target.value))}
              className="w-full accent-primary"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="ri-questions">Questions asked (optional)</Label>
            <Textarea
              id="ri-questions"
              value={questionsAsked}
              onChange={(e) => setQuestionsAsked(e.target.value)}
              placeholder="Any questions you remember being asked, one per line..."
              rows={3}
            />
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-3">
          <Button
            type="button"
            variant="secondary"
            onClick={() => onOpenChange(false)}
            disabled={isSaving}
          >
            Cancel
          </Button>
          <Button type="button" onClick={handleSave} disabled={isSaving || !howItWent.trim()}>
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <MessageSquarePlus className="mr-2 h-4 w-4" />
                Save log
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
