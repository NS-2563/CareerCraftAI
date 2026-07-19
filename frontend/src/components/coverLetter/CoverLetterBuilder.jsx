import { useState, useEffect, useRef, useCallback } from "react";
import CoverLetterToolbar from "./CoverLetterToolbar";
import CoverLetterPreview from "./CoverLetterPreview";
import {
  listCoverLetters,
  getCoverLetter,
  createCoverLetter,
  updateCoverLetter,
  deleteCoverLetter,
  duplicateCoverLetter,
  renameCoverLetter,
  generateCoverLetter,
  applyEditCoverLetter,
} from "@/services/coverLetterApi";
import { listResumes } from "@/resume/services/resumeApi";

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
  const [coverLetters, setCoverLetters] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [coverLetter, setCoverLetter] = useState(initialCoverLetter);
  const [resumes, setResumes] = useState([]);
  const [versions, setVersions] = useState([]);

  // Loading states
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  // Error state
  const [error, setError] = useState(null);

  const previewRef = useRef(null);

  // Load cover letters on mount
  useEffect(() => {
    loadCoverLetters();
    loadResumes();
  }, []);

  async function loadCoverLetters() {
    setIsLoading(true);
    setError(null);
    try {
      const result = await listCoverLetters(null, null);
      if (result.success) {
        setCoverLetters(result.data || []);
        // Select first if none selected
        if (!selectedId && result.data?.length > 0) {
          selectCoverLetter(result.data[0].id);
        }
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    }
    setIsLoading(false);
  }

  async function loadResumes() {
    try {
      const result = await listResumes(null, null);
      if (result.success) {
        setResumes(result.data || []);
      }
    } catch (err) {
      console.error("Failed to load resumes:", err);
    }
  }

  const selectCoverLetter = async (id) => {
    setIsLoading(true);
    try {
      const result = await getCoverLetter(id, null);
      if (result.success) {
        setSelectedId(id);
        setCoverLetter(result.data);
        // Load version history
        const versionResult = await loadVersionHistory(id);
        setVersions(versionResult);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    }
    setIsLoading(false);
  };

  const loadVersionHistory = async (id) => {
    try {
      const result = await getVersionHistory(id, null);
      return result.success ? result.data || [] : [];
    } catch {
      return [];
    }
  };

  // Create new cover letter
  const handleCreate = async () => {
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
  };

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

    await loadCoverLetters();
  }

  setIsGenerating(true);

  try {
    const request = {
      resume_id: coverLetter.resume_id,
      job_title: coverLetter.job_title,
      company_name: coverLetter.company_name,
      job_description: coverLetter.job_description,
      tone: coverLetter.tone,
    };

    const result = await generateCoverLetter(request, null);

    if (result.success) {
      const updateResult = await updateCoverLetter(
        id,
        {
          ...coverLetter,
          content: result.data.content,
        },
        null
      );

      if (updateResult.success) {
        setCoverLetter(updateResult.data);
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
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    }
    setIsGenerating(false);
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
      />

      {error && (
        <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 text-red-600 rounded-md">
          {error}
        </div>
      )}

      {/* Cover Letter List Sidebar */}
      <div className="grid lg:grid-cols-12 gap-6 p-6">
        <aside className="lg:col-span-2 rounded-xl border p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Cover Letters</h2>
            <button
              className="w-8 h-8 flex items-center justify-center rounded-md border hover:bg-accent"
              onClick={handleCreate}
              title="New Cover Letter"
            >
              +
            </button>
          </div>

          <div className="space-y-2">
            {coverLetters.map((cl) => (
              <button
                key={cl.id}
                className={`w-full text-left p-3 rounded-lg border transition-all ${
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
              <div className="text-sm text-muted-foreground p-4 text-center">
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

