import { useState } from "react";
import { Loader2 } from "lucide-react";

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

export default function LinkResumeDialog({
  open,
  onOpenChange,
  job,
  resumes,
  loading,
  onLink,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Link a Resume</DialogTitle>
          <DialogDescription>
            Choose the resume used for this application. It will also be used as
            the default for the cover letter and JD match.
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading resumes...
          </div>
        ) : resumes.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            You don't have any resumes yet. Create one in the Resume Studio
            first.
          </p>
        ) : (
          <ResumePicker job={job} resumes={resumes} onLink={onLink} />
        )}

        <DialogFooter className="gap-2 sm:gap-3">
          <Button
            type="button"
            variant="secondary"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ResumePicker({ job, resumes, onLink }) {
  const [selectedId, setSelectedId] = useState(
    Number(job?.resume_id) ? String(job.resume_id) : ""
  );

  return (
    <div className="space-y-2">
      <Label htmlFor="resume-picker">Resume</Label>
      <select
        id="resume-picker"
        className="h-9 w-full rounded-md border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        value={selectedId}
        onChange={(e) => setSelectedId(e.target.value)}
      >
        <option value="" disabled>
          Select a resume...
        </option>
        {resumes.map((r) => (
          <option key={r.id} value={r.id}>
            {r.name || `Resume ${r.id}`}
          </option>
        ))}
      </select>
      <div className="pt-1">
        <Button
          type="button"
          disabled={!selectedId}
          onClick={() => onLink(Number(selectedId))}
        >
          Link Resume
        </Button>
      </div>
    </div>
  );
}
