import { useState } from "react";
import { Link } from "react-router-dom";
import { Briefcase, CalendarClock, Cpu, FileText, Link2, Unlink } from "lucide-react";

import { Bar, SectionLabel, StatusBadge } from "@/components/ui/atoms";
import { cn } from "@/lib/utils";

const fmtDateTime = (iso) => {
  if (!iso) return "Not recorded";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "Not recorded";
  return `${d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })} · ${d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}`;
};

function MetaRow({ icon: Icon, label, children }) {
  return (
    <div className="flex items-start gap-2">
      <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <div className="text-sm">{children}</div>
      </div>
    </div>
  );
}

/**
 * Real generation metadata footer for the output view.
 *
 * Shows only stored facts: tone, the actual AI provider/model used, when the
 * letter was generated, the linked resume, the deterministic ATS keyword
 * coverage count, and the linked job application (with a way to set it).
 * No invented quality scores.
 */
export default function CoverLetterMetadata({
  coverLetter,
  resumes = [],
  jobs = [],
  atsCoverage,
  onLinkJobApplication,
}) {
  const [showKeywordDetails, setShowKeywordDetails] = useState(false);
  const [linkJobId, setLinkJobId] = useState("");

  const resume = (resumes || []).find((r) => r.id === coverLetter?.resume_id);
  const linkedJob = (jobs || []).find((j) => j.id === coverLetter?.job_application_id);

  const hasMetadata = Boolean(coverLetter?.ai_provider || coverLetter?.model_name || coverLetter?.generated_at);
  const coverage = atsCoverage || {};
  const total = coverage.total_keywords || 0;
  const covered = coverage.covered_count || 0;
  const coveragePct = total > 0 ? Math.round((covered / total) * 100) : 0;

  const handleLink = () => {
    const id = Number(linkJobId);
    if (id && onLinkJobApplication) onLinkJobApplication(id);
    setLinkJobId("");
  };

  return (
    <div className="rounded-xl border p-5">
      <SectionLabel className="mb-3">What informed this letter</SectionLabel>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-3">
          <MetaRow icon={FileText} label="Tone">
            <StatusBadge status={coverLetter?.tone || "professional"} />
          </MetaRow>

          <MetaRow icon={Cpu} label="Generated with">
            {hasMetadata ? (
              <span className="font-mono text-xs">
                {[coverLetter?.ai_provider, coverLetter?.model_name].filter(Boolean).join(" · ")}
              </span>
            ) : (
              <span className="text-muted-foreground">Not recorded (created manually or before metadata tracking)</span>
            )}
          </MetaRow>

          <MetaRow icon={CalendarClock} label="Generated at">
            {fmtDateTime(coverLetter?.generated_at)}
          </MetaRow>

          <MetaRow icon={FileText} label="Linked resume">
            {resume ? (
              <Link
                to={`/resume-studio?resume=${coverLetter.resume_id}`}
                className="text-primary hover:underline"
              >
                {resume.name || `Resume ${resume.id}`}
              </Link>
            ) : (
              <span className="text-muted-foreground">None</span>
            )}
          </MetaRow>
        </div>

        <div className="space-y-3">
          {/* ATS keyword coverage — real count, not a quality score */}
          <div>
            <p className="text-xs text-muted-foreground">ATS keyword coverage</p>
            <div className="mt-1 flex items-center justify-between gap-2">
              <span className="text-sm font-medium tabular-nums">
                {coverage.label || "No job description to check"}
              </span>
              {total > 0 && (
                <span className="text-xs text-muted-foreground tabular-nums">
                  {covered}/{total}
                </span>
              )}
            </div>
            <Bar value={coveragePct} accent={coveragePct >= 50 ? "var(--emerald)" : "var(--amber)"} className="mt-1.5" />
            {total > 0 && (
              <button
                type="button"
                onClick={() => setShowKeywordDetails((s) => !s)}
                className="mt-1.5 text-xs font-medium text-muted-foreground hover:text-foreground"
              >
                {showKeywordDetails ? "Hide" : "Show"} which keywords
              </button>
            )}
            {total > 0 && showKeywordDetails && (
              <div className="mt-2 space-y-2 text-xs">
                {coverage.covered_keywords?.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {(coverage.covered_keywords || []).map((kw) => (
                      <span key={kw} className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-emerald-700 dark:text-emerald-300">
                        {kw}
                      </span>
                    ))}
                  </div>
                )}
                {coverage.missing_keywords?.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {(coverage.missing_keywords || []).map((kw) => (
                      <span key={kw} className="rounded-full border px-2 py-0.5 text-muted-foreground">
                        {kw}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Job application link */}
          <div>
            <p className="text-xs text-muted-foreground">Job application</p>
            {linkedJob ? (
              <Link
                to="/jobs"
                className="mt-1 inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
              >
                <Briefcase className="size-4" />
                {linkedJob.job_title || "Role"} @ {linkedJob.company || "Company"}
                <StatusBadge status={linkedJob.status} />
              </Link>
            ) : (
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <select
                  value={linkJobId}
                  onChange={(e) => setLinkJobId(e.target.value)}
                  className="h-8 rounded-md border border-input bg-transparent px-2 text-sm"
                  aria-label="Link to job application"
                >
                  <option value="">Link to an application…</option>
                  {(jobs || []).map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.job_title || "Role"} @ {j.company || "Company"}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={handleLink}
                  disabled={!linkJobId}
                  className={cn(
                    "inline-flex h-8 items-center gap-1.5 rounded-md border px-2.5 text-sm hover:bg-accent disabled:opacity-50",
                  )}
                >
                  <Link2 className="size-3.5" />
                  Link
                </button>
                {jobs.length === 0 && (
                  <span className="text-xs text-muted-foreground">
                    <Link to="/jobs" className="text-primary hover:underline">Create a job application</Link> to link it here.
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {coverLetter?.job_application_id && (
        <button
          type="button"
          onClick={() => onLinkJobApplication?.(null)}
          className="mt-3 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <Unlink className="size-3.5" />
          Unlink application
        </button>
      )}
    </div>
  );
}
