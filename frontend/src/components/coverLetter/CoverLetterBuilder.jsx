import { useState, useEffect, useRef, useCallback } from "react";
import { Link, useSearchParams } from "react-router-dom";
import CoverLetterToolbar from "./CoverLetterToolbar";
import CoverLetterPreview from "./CoverLetterPreview";
import CoverLetterChecklist from "./CoverLetterChecklist";
import CoverLetterMetadata from "./CoverLetterMetadata";
import CoverLetterDiffView from "./CoverLetterDiffView";
import {
  listCoverLetters,
  getCoverLetter,
  createCoverLetter,
  updateCoverLetter,
  deleteCoverLetter,
  duplicateCoverLetter,
  renameCoverLetter,
  generateCoverLetterForExisting,
  applyEditCoverLetter,
  getCoverLetterDiff,
  getAtsCoverage,
} from "@/services/coverLetterApi";
import { listResumes } from "@/services/resumeApi";
import { getJobs } from "@/modules/jobTracker/api/jobTrackerApi";
import { SuccessBanner } from "@/components/ui/atoms";

const initialCoverLetter = {
  title: "Untitled Cover Letter",
  content: "",
  job_title: "",
  company_name: "",
  job_description: "",
  tone: "professional",
  template: "modern",
  resume_id: null,
};

export default function CoverLetterBuilder() {
  const [searchParams] = useSearchParams();
  const paramHandledRef = useRef(false);

  const [coverLetters, setCoverLetters] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [coverLetter, setCoverLetter] = useState(initialCoverLetter);
  const [resumes, setResumes] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [, setVersions] = useState([]);

  // Transparency state
  const [generateReady, setGenerateReady] = useState(false);
  const [atsCoverage, setAtsCoverage] = useState(null);
  const [diffData, setDiffData] = useState(null);

  // Loading states
  const [isSaving, setIsSaving] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  // Error state
  const [error, setError] = useState(null);

  // Post-AI success banner
  const [justGenerated, setJustGenerated] = useState(false);

  const previewRef = useRef(null);

  const loadVersionHistory = useCallback(async (id) => {
    try {
      const result = await getVersionHistory(id, null);
      return result.success ? result.data || [] : [];
    } catch {
      return [];
    }
  }, []);

  const refreshCoverage = useCallback(async (id) => {
    if (!id) {
      setAtsCoverage(null);
      return;
    }
    try {
      const result = await getAtsCoverage(id);
      setAtsCoverage(result.success ? result.data : null);
    } catch {
      setAtsCoverage(null);
    }
  }, []);

  const loadDiff = useCallback(async (id, fromVersion, toVersion) => {
    if (!id || !fromVersion || !toVersion) {
      setDiffData(null);
      return;
    }
    try {
      const result = await getCoverLetterDiff(id, fromVersion, toVersion);
      setDiffData(result.success ? result.data : null);
    } catch {
      setDiffData(null);
    }
  }, []);

  const selectCoverLetter = useCallback(
    async (id) => {
      try {
        const result = await getCoverLetter(id, null);
        if (result.success) {
          setSelectedId(id);
          setCoverLetter(result.data);
          // Load version history
          const versionResult = await loadVersionHistory(id);
          setVersions(versionResult);
          refreshCoverage(id);
          setDiffData(null);
        } else {
          setError(result.error);
        }
      } catch (err) {
        setError(err.message);
      }
    },
    [loadVersionHistory, refreshCoverage]
  );

  const loadCoverLetters = useCallback(async () => {
    try {
      const result = await listCoverLetters(null, null);
      if (result.success) {
        setError(null);
        setCoverLetters(result.data || []);
        // Select first if none selected
        if (!selectedId && result.data?.length > 0) {
          selectCoverLetter(result.data[0].id);
        }
      } else {
        setError(result.error);
      }
    } finally {
      // errors are handled by the caller's .catch
    }
  }, [selectedId, selectCoverLetter]);

  const loadResumes = useCallback(async () => {
    try {
      const result = await listResumes(null, null);
      if (Array.isArray(result)) {
        setResumes(result);
      }
    } finally {
      // errors handled by the caller's .catch
    }
  }, []);

  const loadJobs = useCallback(async () => {
    try {
      const data = await getJobs({ sort_by: "created_at", descending: true });
      setJobs(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load jobs:", err);
    }
  }, []);

  // Load cover letters on mount
  useEffect(() => {
    (async () => {
      try {
        await loadCoverLetters();
      } catch (err) {
        setError(err.message);
      }
      try {
        await loadResumes();
      } catch (err) {
        console.error("Failed to load resumes:", err);
      }
      try {
        await loadJobs();
      } catch (err) {
        console.error("Failed to load jobs:", err);
      }
    })();
  }, [loadCoverLetters, loadResumes, loadJobs]);

  // Create new cover letter
  const handleCreate = useCallback(async () => {
    setIsSaving(true);
    try {
      const result = await createCoverLetter(initialCoverLetter, null);
      if (result.success) {
        await loadCoverLetters();
        selectCoverLetter(result.data.id);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    }
    setIsSaving(false);
  }, [loadCoverLetters, selectCoverLetter]);

  // Deep-link support: ?id= opens a saved letter, ?create=1 starts a new one
  useEffect(() => {
    if (paramHandledRef.current || coverLetters.length === 0) return;
    paramHandledRef.current = true;
    const requestedId = Number(searchParams.get("id"));
    (async () => {
      if (requestedId) {
        const target = coverLetters.find((c) => c.id === requestedId);
        if (target) await selectCoverLetter(requestedId);
      } else if (searchParams.get("create") === "1" && !selectedId) {
        await handleCreate();
      }
    })();
  }, [coverLetters, searchParams, selectedId, selectCoverLetter, handleCreate]);

  // Save current cover letter
  const handleSave = async () => {
    if (!selectedId) {
      await handleCreate();
      return;
    }

    setIsSaving(true);
    try {
      const result = await updateCoverLetter(selectedId, coverLetter, null);
      if (result.success) {
        setCoverLetter(result.data);
        await loadCoverLetters();
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    }
    setIsSaving(false);
  };

  // Delete cover letter
  const handleDelete = async () => {
    if (!selectedId) return;

    setIsSaving(true);
    try {
      const result = await deleteCoverLetter(selectedId, null);
      if (result.success) {
        setSelectedId(null);
        setCoverLetter(initialCoverLetter);
        await loadCoverLetters();
        // Select first if available
        if (coverLetters.length > 1) {
          const first = coverLetters.find((c) => c.id !== selectedId);
          if (first) selectCoverLetter(first.id);
        }
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    }
    setIsSaving(false);
  };

  // Duplicate cover letter
  const handleDuplicate = async () => {
    if (!selectedId) return;

    setIsSaving(true);
    try {
      const newTitle = `${coverLetter.title} (Copy)`;
      const result = await duplicateCoverLetter(selectedId, newTitle, null);
      if (result.success) {
        await loadCoverLetters();
        selectCoverLetter(result.data.id);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    }
    setIsSaving(false);
  };

  // Rename cover letter
  const handleRename = async (newTitle) => {
    if (!selectedId) return;

    setIsSaving(true);
    try {
      const result = await renameCoverLetter(selectedId, newTitle, null);
      if (result.success) {
        setCoverLetter(result.data);
        await loadCoverLetters();
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    }
    setIsSaving(false);
  };

  // Generate with AI
const handleGenerate = async () => {
  if (!generateReady) return;

  let id = selectedId;

  if (!id) {
    const createResult = await createCoverLetter(initialCoverLetter, null);

    if (!createResult.success) {
      setError(createResult.error);
      return;
    }

    id = createResult.data.id;

    setSelectedId(id);
    setCoverLetter(createResult.data);

    try {
      await loadCoverLetters();
    } catch (err) {
      setError(err.message);
    }
  }

  if (!coverLetter.job_title?.trim()) {
    setError("Please enter a job title before generating a cover letter.");
    setIsGenerating(false);
    return;
  }
  if (!coverLetter.company_name?.trim()) {
    setError("Please enter a company name before generating a cover letter.");
    setIsGenerating(false);
    return;
  }

  setIsGenerating(true);

  const previousVersion = coverLetter.version || 1;

  try {
    const request = {
      resume_id: coverLetter.resume_id,
      job_title: coverLetter.job_title,
      company_name: coverLetter.company_name,
      job_description: coverLetter.job_description,
      tone: coverLetter.tone,
    };

    const result = await generateCoverLetterForExisting(id, request, null);

    if (result.success) {
      setCoverLetter(result.data);
      setJustGenerated(true);
      await refreshCoverage(id);
      if (previousVersion !== result.data.version) {
        await loadDiff(id, previousVersion, result.data.version);
      }
    } else {
      setError(result.error);
    }
  } catch (err) {
    setError(err.message);
  }

  setIsGenerating(false);
};

  // AI Edit
  const handleEdit = async (action) => {
    if (!selectedId || !coverLetter.content) return;

    setIsGenerating(true);
    const previousVersion = coverLetter.version || 1;
    try {
      const request = {
        action,
        content: coverLetter.content,
        job_title: coverLetter.job_title,
        company_name: coverLetter.company_name,
      };

      const result = await applyEditCoverLetter(selectedId, request, null);
      if (result.success) {
        setCoverLetter(result.data);
        setJustGenerated(true);
        await refreshCoverage(selectedId);
        if (previousVersion !== result.data.version) {
          await loadDiff(selectedId, previousVersion, result.data.version);
        }
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    }
    setIsGenerating(false);
  };

  // Link / unlink a job application
  const handleLinkJobApplication = async (jobId) => {
    if (!selectedId) return;
    setIsSaving(true);
    try {
      const result = await updateCoverLetter(
        selectedId,
        { ...coverLetter, job_application_id: jobId },
        null
      );
      if (result.success) {
        setCoverLetter(result.data);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    }
    setIsSaving(false);
  };

  // Template/Tone change
  const handleTemplateChange = (template) => {
    setCoverLetter((prev) => ({ ...prev, template }));
  };

  const handleToneChange = (tone) => {
    setCoverLetter((prev) => ({ ...prev, tone }));
  };

  // Export
  const handleExport = useCallback((format) => {
    if (!previewRef.current) return;

    setIsExporting(true);
    try {
      if (format === "pdf") {
        // Use browser print to PDF
        window.print();
      } else if (format === "docx") {
        // Simple text download as fallback
        const blob = new Blob([coverLetter.content || ""], {
          type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${coverLetter.title || "cover-letter"}.docx`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      setError(err.message);
    }
    setIsExporting(false);
  }, [coverLetter.content, coverLetter.title]);

  // Field changes
  const handleFieldChange = (field, value) => {
    setCoverLetter((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="min-h-screen bg-background">
      <CoverLetterToolbar
        coverLetter={coverLetter}
        onSave={handleSave}
        onDelete={handleDelete}
        onDuplicate={handleDuplicate}
        onRename={handleRename}
        onTemplateChange={handleTemplateChange}
        onToneChange={handleToneChange}
        onExport={handleExport}
        onGenerate={handleGenerate}
        onEdit={handleEdit}
        isGenerating={isGenerating}
        isSaving={isSaving}
        isExporting={isExporting}
        canGenerate={generateReady}
      />

      {error && (
        <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 text-red-600 rounded-md">
          {error}
        </div>
      )}

      {justGenerated && (
        <SuccessBanner
          onDismiss={() => setJustGenerated(false)}
          className="mx-6 mt-4"
        >
          Cover letter {coverLetter.title ? `“${coverLetter.title}”` : "draft"} generated from
          your resume and the job details you provided.
        </SuccessBanner>
      )}

      {/* Cover Letter List Sidebar */}
      <div className="grid lg:grid-cols-12 gap-4 sm:gap-6 p-4 sm:p-6">
        <aside className="lg:col-span-2 rounded-xl border p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Cover Letters</h2>
            <div className="flex items-center gap-2">
              <Link
                to="/cover-letter-library"
                className="text-xs text-primary hover:underline"
              >
                Library
              </Link>
              <button
                className="w-8 h-8 flex items-center justify-center rounded-md border hover:bg-accent"
                onClick={handleCreate}
                title="New Cover Letter"
              >
                +
              </button>
            </div>
          </div>

          <div className="flex lg:flex-col gap-2 overflow-x-auto pb-2">
            {coverLetters.map((cl) => (
              <button
                key={cl.id}
                className={`shrink-0 w-56 lg:w-full text-left p-3 rounded-lg border transition-all ${
                  selectedId === cl.id
                    ? "bg-primary/5 border-primary shadow-sm"
                    : "hover:border-primary/50"
                }`}
                onClick={() => selectCoverLetter(cl.id)}
              >
                <div className="font-medium truncate">{cl.title}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {cl.template} - {cl.tone}
                </div>
                <div className="text-xs text-muted-foreground">
                  v{cl.version} •{" "}
                  {cl.updated_at
                    ? new Date(cl.updated_at).toLocaleDateString()
                    : "New"}
                </div>
              </button>
            ))}

            {coverLetters.length === 0 && (
              <div className="text-sm text-muted-foreground p-4 text-center w-full">
                No cover letters yet.
                <br />
                Click + to create one.
              </div>
            )}
          </div>
        </aside>

        {/* Editor (left) */}
        <main className="lg:col-span-5 rounded-xl border p-6">
          <h2 className="text-xl font-semibold mb-6">Cover Letter Details</h2>

          <div className="space-y-4">
            {/* Resume Selection */}
            <div>
              <label className="block text-sm font-medium mb-2">Resume (Optional)</label>
              <select
                value={coverLetter.resume_id || ""}
                onChange={(e) =>
                  handleFieldChange(
                    "resume_id",
                    e.target.value ? parseInt(e.target.value) : null
                  )
                }
                className="w-full border rounded-md px-3 py-2"
              >
                <option value="">Select a resume...</option>
                {resumes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name || `Resume ${r.id}`}
                  </option>
                ))}
              </select>
              <p className="text-xs text-muted-foreground mt-1">
                AI will use your resume data to generate the cover letter.
              </p>
            </div>

            {/* Job Title */}
            <div>
              <label className="block text-sm font-medium mb-2">Job Title *</label>
              <input
                type="text"
                value={coverLetter.job_title || ""}
                onChange={(e) => handleFieldChange("job_title", e.target.value)}
                placeholder="e.g., Software Engineer"
                className="w-full border rounded-md px-3 py-2"
                required
              />
            </div>

            {/* Company Name */}
            <div>
              <label className="block text-sm font-medium mb-2">Company Name *</label>
              <input
                type="text"
                value={coverLetter.company_name || ""}
                onChange={(e) => handleFieldChange("company_name", e.target.value)}
                placeholder="e.g., Google"
                className="w-full border rounded-md px-3 py-2"
                required
              />
            </div>

            {/* Job Description */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Job Description (Optional)
              </label>
              <textarea
                value={coverLetter.job_description || ""}
                onChange={(e) => handleFieldChange("job_description", e.target.value)}
                placeholder="Paste the job description..."
                rows={4}
                className="w-full border rounded-md px-3 py-2 resize-none"
              />
              <p className="text-xs text-muted-foreground mt-1">
                AI will match your skills to the requirements.
              </p>
            </div>

            {/* Missing-info checklist (gates Generate) */}
            <CoverLetterChecklist
              resumeId={coverLetter.resume_id}
              jobTitle={coverLetter.job_title}
              companyName={coverLetter.company_name}
              jobDescription={coverLetter.job_description}
              onReadyChange={setGenerateReady}
            />

            {/* Content Editor */}
            <div>
              <label className="block text-sm font-medium mb-2">Cover Letter Content</label>
              <textarea
                value={coverLetter.content || ""}
                onChange={(e) => handleFieldChange("content", e.target.value)}
                placeholder="Write your cover letter here or click 'Generate AI' to create one with AI..."
                rows={12}
                className="w-full border rounded-md px-3 py-2 resize-none font-mono text-sm"
              />
            </div>

            {/* AI Edit Actions */}
            {coverLetter.content && (
              <div>
                <label className="block text-sm font-medium mb-2">AI Editing</label>
                <div className="flex flex-wrap gap-2">
                  <button
                    className="px-3 py-1.5 text-sm border rounded-md hover:bg-accent"
                    onClick={() => handleEdit("improve")}
                    disabled={isGenerating}
                  >
                    Improve
                  </button>
                  <button
                    className="px-3 py-1.5 text-sm border rounded-md hover:bg-accent"
                    onClick={() => handleEdit("rewrite")}
                    disabled={isGenerating}
                  >
                    Rewrite
                  </button>
                  <button
                    className="px-3 py-1.5 text-sm border rounded-md hover:bg-accent"
                    onClick={() => handleEdit("shorten")}
                    disabled={isGenerating}
                  >
                    Shorten
                  </button>
                  <button
                    className="px-3 py-1.5 text-sm border rounded-md hover:bg-accent"
                    onClick={() => handleEdit("expand")}
                    disabled={isGenerating}
                  >
                    Expand
                  </button>
                  <button
                    className="px-3 py-1.5 text-sm border rounded-md hover:bg-accent"
                    onClick={() => handleEdit("grammar_fix")}
                    disabled={isGenerating}
                  >
                    Fix Grammar
                  </button>
                  <button
                    className="px-3 py-1.5 text-sm border rounded-md hover:bg-accent"
                    onClick={() => handleEdit("ats_optimize")}
                    disabled={isGenerating}
                  >
                    ATS Optimize
                  </button>
                </div>
              </div>
            )}
          </div>
        </main>

        {/* Preview (right) */}
        <section className="lg:col-span-5 rounded-xl border p-6 bg-gray-50">
          <h2 className="text-xl font-semibold mb-6">Preview</h2>

          <CoverLetterPreview
            ref={previewRef}
            template={coverLetter.template}
            content={coverLetter.content}
            personalInfo={coverLetter.personal_info || {}}
          />

          {!generateReady && coverLetter.resume_id && (
            <p className="mt-4 text-xs text-amber-600 dark:text-amber-400">
              Generation is disabled until the job title and company name are
              filled in.
            </p>
          )}

          {selectedId && coverLetter.content && (
            <div className="mt-4 space-y-4">
              <CoverLetterMetadata
                coverLetter={coverLetter}
                resumes={resumes}
                jobs={jobs}
                atsCoverage={atsCoverage}
                onLinkJobApplication={handleLinkJobApplication}
              />
              {diffData && <CoverLetterDiffView diff={diffData} />}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

// Helper to get version history
async function getVersionHistory(coverLetterId, signal) {
  const { getVersionHistory: getVersions } = await import("@/services/coverLetterApi");
  return getVersions(coverLetterId, signal);
}

