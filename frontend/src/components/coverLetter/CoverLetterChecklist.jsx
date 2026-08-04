import { useEffect, useState } from "react";
import { preflightCoverLetter } from "@/services/coverLetterApi";
import { ChecklistProgress } from "@/components/ui/atoms";

const CHECK_ITEMS = [
  { key: "resume", label: "Resume selected" },
  { key: "job title", label: "Job title" },
  { key: "company name", label: "Company name" },
  { key: "job description", label: "Job description text" },
];

/**
 * Missing-information checklist for the generation view.
 *
 * Calls the backend's deterministic pre-flight endpoint (debounced) and renders
 * exactly which required inputs are present vs missing. The parent uses
 * ``onReadyChange`` to gate the Generate button on real backend data.
 */
export default function CoverLetterChecklist({
  resumeId,
  jobTitle,
  companyName,
  jobDescription,
  onReadyChange,
}) {
  const [missing, setMissing] = useState([]);

  useEffect(() => {
    let active = true;
    const timer = setTimeout(async () => {
      const result = await preflightCoverLetter({
        resume_id: resumeId,
        job_title: jobTitle,
        company_name: companyName,
        job_description: jobDescription,
      });
      if (!active) return;
      const missingList = result.success ? result.data?.missing || [] : [];
      setMissing(missingList);
      onReadyChange?.(missingList.length === 0);
    }, 350);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [resumeId, jobTitle, companyName, jobDescription, onReadyChange]);

  const missingSet = new Set(missing);
  const items = CHECK_ITEMS.map((c) => ({ label: c.label, done: !missingSet.has(c.key) }));
  const doneCount = items.filter((i) => i.done).length;

  return (
    <div className="rounded-lg border p-4">
      <ChecklistProgress
        label="Required for generation"
        items={items}
        value={Math.round((doneCount / items.length) * 100)}
      />
      {doneCount === items.length ? (
        <p className="mt-2 text-xs text-muted-foreground">
          All required inputs are ready. You can generate your cover letter.
        </p>
      ) : (
        <p className="mt-2 text-xs text-muted-foreground">
          Provide the missing inputs to enable AI generation.
        </p>
      )}
    </div>
  );
}
