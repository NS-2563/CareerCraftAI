import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";

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

import {
  generateCoverLetter,
  createCoverLetter,
} from "@/services/coverLetterApi";

export default function GenerateCoverLetterDialog({
  open,
  onOpenChange,
  job,
  resumes,
  loading,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Generate a Cover Letter</DialogTitle>
          <DialogDescription>
            Reusing the cover letter generation flow for{" "}
            {job?.company || "this application"} — the result will be linked to
            this application.
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading resumes...
          </div>
        ) : (
          <GeneratorForm
            job={job}
            resumes={resumes}
            onDone={() => onOpenChange(false)}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}

function GeneratorForm({ job, resumes, onDone }) {
  const [resumeId, setResumeId] = useState(
    Number(job?.resume_id) ? String(job.resume_id) : ""
  );
  const [tone, setTone] = useState("professional");
  const [jobDescription, setJobDescription] = useState(
    job?.job_description || ""
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);

  async function handleGenerate() {
    setError(null);
    setIsGenerating(true);

    const request = {
      resume_id: resumeId ? Number(resumeId) : null,
      job_title: job?.job_title || "",
      company_name: job?.company || "",
      job_description: jobDescription || null,
      tone,
    };

    try {
      const generated = await generateCoverLetter(request);
      if (!generated.success) {
        setError(generated.error);
        return;
      }

      const createResult = await createCoverLetter({
        resume_id: resumeId ? Number(resumeId) : null,
        job_application_id: job?.id ?? null,
        content: generated.data.content,
        job_title: job?.job_title || "",
        company_name: job?.company || "",
        job_description: jobDescription || null,
        tone,
        title: `Cover letter for ${job?.company || "this application"}`,
      });

      if (!createResult.success) {
        setError(createResult.error);
        return;
      }

      onDone();
    } catch (err) {
      setError(err?.message || "Failed to generate cover letter.");
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <div className="space-y-4">
      {error ? (
        <Alert variant="destructive">
          <AlertTitle>Generation failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <div className="space-y-2">
        <Label htmlFor="cl-resume">Resume</Label>
        <select
          id="cl-resume"
          className="h-9 w-full rounded-md border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
          value={resumeId}
          onChange={(e) => setResumeId(e.target.value)}
        >
          <option value="">No resume selected</option>
          {resumes.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name || `Resume ${r.id}`}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="cl-tone">Tone</Label>
        <select
          id="cl-tone"
          className="h-9 w-full rounded-md border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
          value={tone}
          onChange={(e) => setTone(e.target.value)}
        >
          <option value="professional">Professional</option>
          <option value="friendly">Friendly</option>
          <option value="enthusiastic">Enthusiastic</option>
          <option value="formal">Formal</option>
        </select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="cl-jd">Job Description (optional)</Label>
        <Textarea
          id="cl-jd"
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Paste the job description to tailor the letter..."
          rows={4}
        />
      </div>

      <DialogFooter className="gap-2 sm:gap-3">
        <Button
          type="button"
          variant="secondary"
          onClick={() => onDone()}
          disabled={isGenerating}
        >
          Cancel
        </Button>
        <Button
          type="button"
          onClick={handleGenerate}
          disabled={isGenerating || !job?.job_title || !job?.company}
        >
          {isGenerating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              Generate
            </>
          )}
        </Button>
      </DialogFooter>
    </div>
  );
}
