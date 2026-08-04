import { useState, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, AlertCircle, CheckCircle } from "lucide-react";
import { toast } from "sonner";

import { saveResume } from "@/services/resumeApi";
import { mapResumePayloadForBackend } from "@/utils/resumeDataCompat";
import { useQueryClient } from "@tanstack/react-query";

import ReviewSection from "./ReviewSection";
import ReviewField from "./ReviewField";
import ReviewSkills from "./ReviewSkills";
import ReviewArraySection from "./ReviewArraySection";

const ARRAY_SECTIONS = [
  "experience", "education", "projects", "certifications",
  "languages", "interests", "references",
];

const SECTION_TITLES = {
  personal: "Personal Information",
  summary: "Summary",
  experience: "Experience",
  education: "Education",
  skills: "Skills",
  projects: "Projects",
  certifications: "Certifications",
  languages: "Languages",
  interests: "Interests",
  references: "References",
};

const PERSONAL_FIELDS = [
  { key: "firstName", label: "First Name", type: "text" },
  { key: "lastName", label: "Last Name", type: "text" },
  { key: "title", label: "Title", type: "text" },
  { key: "email", label: "Email", type: "text" },
  { key: "phone", label: "Phone", type: "text" },
  { key: "location", label: "Location", type: "text" },
  { key: "linkedin", label: "LinkedIn", type: "text" },
  { key: "github", label: "GitHub", type: "text" },
  { key: "portfolio", label: "Portfolio", type: "text" },
];

export default function ImportReviewStep({
  parsedData,
  sourceMeta,
  resumeName,
  onCancel,
}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(() => structuredClone(parsedData));
  const [editedFields, setEditedFields] = useState({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  const sectionAiStatus = useMemo(() => {
    if (!sourceMeta) return {};
    const status = {};
    for (const [section, meta] of Object.entries(sourceMeta)) {
      if (meta?.ai_success) {
        status[section] = true;
      }
    }
    return status;
  }, [sourceMeta]);

  const handleFieldChange = useCallback((section, field, value) => {
    setEditing((prev) => {
      const next = { ...prev };
      if (section === "personal") {
        next.personal = { ...(next.personal || {}), [field]: value };
      } else if (section === "summary") {
        next.summary = value;
      }
      return next;
    });
    setEditedFields((prev) => ({
      ...prev,
      [`${section}.${field}`]: true,
    }));
  }, []);

  const handleArrayUpdate = useCallback((section, items) => {
    setEditing((prev) => ({ ...prev, [section]: items }));
    setEditedFields((prev) => ({
      ...prev,
      [`${section}._updated`]: true,
    }));
  }, []);

  const handleSave = useCallback(async (openInStudio) => {
    setSaving(true);
    setSaveError(null);

    const effectiveName = editing._name || resumeName;

    try {
      const clean = {};
      for (const key of Object.keys(editing)) {
        if (!key.startsWith("_")) {
          clean[key] = editing[key];
        }
      }

      const backendPayload = mapResumePayloadForBackend(clean);
      const response = await saveResume({
        name: effectiveName,
        ...backendPayload,
      });

      const newId = response?.id;
      if (!newId) {
        throw new Error("No resume ID returned from server");
      }

      queryClient.invalidateQueries({ queryKey: ["resumes"] });
      toast.success("Resume saved to library");

      if (openInStudio && newId) {
        navigate(`/resume-studio?id=${newId}`);
      } else {
        onCancel?.();
      }
    } catch (err) {
      const detail =
        err?.response?.data?.detail || err?.message || "Failed to save resume";
      setSaveError(typeof detail === "string" ? detail : "Failed to save resume. Please try again.");
    } finally {
      setSaving(false);
    }
  }, [editing, resumeName, queryClient, navigate, onCancel]);

  const getSource = (section, field) => {
    const src = sourceMeta?.[section]?.sources;
    if (!src) return "";
    if (src[field]) return src[field];
    if (src._all) return src._all;
    return "";
  };

  const isEdited = (section, field) => {
    return !!editedFields[`${section}.${field}`];
  };

  const sectionCounts = useMemo(() => {
    const counts = {};
    for (const s of ARRAY_SECTIONS) {
      const arr = editing[s];
      counts[s] = Array.isArray(arr) ? arr.filter((i) => i && Object.values(i).some((v) => v)).length : 0;
    }
    counts.skills = Array.isArray(editing.skills)
      ? editing.skills.filter((s) => s?.name).length
      : 0;
    return counts;
  }, [editing]);

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Resume Name
        </label>
        <input
          type="text"
          defaultValue={resumeName}
          onChange={(e) => {
            setEditing((prev) => ({ ...prev, _name: e.target.value }));
          }}
          className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary bg-white"
        />
      </div>

      <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
        <ReviewSection
          title={SECTION_TITLES.personal}
          summary={
            editing.personal?.firstName || editing.personal?.email
              ? `${editing.personal.firstName || ""} ${editing.personal.lastName || ""}`.trim() || editing.personal.email
              : "No data"
          }
          aiEnhanced={sectionAiStatus.personal}
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {PERSONAL_FIELDS.map((field) => (
              <ReviewField
                key={field.key}
                label={field.label}
                value={editing.personal?.[field.key] ?? ""}
                source={getSource("personal", field.key)}
                edited={isEdited("personal", field.key)}
                type={field.type}
                onChange={(val) => handleFieldChange("personal", field.key, val)}
              />
            ))}
          </div>
        </ReviewSection>

        <ReviewSection
          title={SECTION_TITLES.summary}
          summary={
            editing.summary
              ? editing.summary.substring(0, 60) + (editing.summary.length > 60 ? "..." : "")
              : "No data"
          }
          aiEnhanced={sectionAiStatus.summary}
        >
          <ReviewField
            label="Professional Summary"
            value={editing.summary ?? ""}
            source={getSource("summary", "summary")}
            edited={isEdited("summary", "summary")}
            type="textarea"
            onChange={(val) => handleFieldChange("summary", "summary", val)}
          />
        </ReviewSection>

        <ReviewSection
          title={SECTION_TITLES.experience}
          summary={sectionCounts.experience > 0 ? `${sectionCounts.experience} entries` : "No entries"}
          aiEnhanced={sectionAiStatus.experience}
        >
          <ReviewArraySection
            section="experience"
            items={editing.experience || []}
            sourceMeta={sourceMeta}
            onUpdate={handleArrayUpdate}
            editedFields={editedFields}
          />
        </ReviewSection>

        <ReviewSection
          title={SECTION_TITLES.education}
          summary={sectionCounts.education > 0 ? `${sectionCounts.education} entries` : "No entries"}
          aiEnhanced={sectionAiStatus.education}
        >
          <ReviewArraySection
            section="education"
            items={editing.education || []}
            sourceMeta={sourceMeta}
            onUpdate={handleArrayUpdate}
            editedFields={editedFields}
          />
        </ReviewSection>

        <ReviewSection
          title={SECTION_TITLES.skills}
          summary={
            sectionCounts.skills > 0
              ? `${sectionCounts.skills} skills`
              : "No skills"
          }
          aiEnhanced={sectionAiStatus.skills}
        >
          <ReviewSkills
            section="skills"
            items={editing.skills || []}
            onUpdate={handleArrayUpdate}
          />
        </ReviewSection>

        <ReviewSection
          title={SECTION_TITLES.projects}
          summary={sectionCounts.projects > 0 ? `${sectionCounts.projects} entries` : "No entries"}
          aiEnhanced={sectionAiStatus.projects}
        >
          <ReviewArraySection
            section="projects"
            items={editing.projects || []}
            sourceMeta={sourceMeta}
            onUpdate={handleArrayUpdate}
            editedFields={editedFields}
          />
        </ReviewSection>

        <ReviewSection
          title={SECTION_TITLES.certifications}
          summary={sectionCounts.certifications > 0 ? `${sectionCounts.certifications} entries` : "No entries"}
          aiEnhanced={sectionAiStatus.certifications}
        >
          <ReviewArraySection
            section="certifications"
            items={editing.certifications || []}
            sourceMeta={sourceMeta}
            onUpdate={handleArrayUpdate}
            editedFields={editedFields}
          />
        </ReviewSection>

        <ReviewSection
          title={SECTION_TITLES.languages}
          summary={sectionCounts.languages > 0 ? `${sectionCounts.languages} entries` : "No entries"}
          aiEnhanced={sectionAiStatus.languages}
        >
          <ReviewArraySection
            section="languages"
            items={editing.languages || []}
            sourceMeta={sourceMeta}
            onUpdate={handleArrayUpdate}
            editedFields={editedFields}
          />
        </ReviewSection>

        <ReviewSection
          title={SECTION_TITLES.interests}
          summary={sectionCounts.interests > 0 ? `${sectionCounts.interests} entries` : "No entries"}
          aiEnhanced={sectionAiStatus.interests}
        >
          <ReviewArraySection
            section="interests"
            items={editing.interests || []}
            sourceMeta={sourceMeta}
            onUpdate={handleArrayUpdate}
            editedFields={editedFields}
          />
        </ReviewSection>

        <ReviewSection
          title={SECTION_TITLES.references}
          summary={sectionCounts.references > 0 ? `${sectionCounts.references} entries` : "No entries"}
          aiEnhanced={sectionAiStatus.references}
        >
          <ReviewArraySection
            section="references"
            items={editing.references || []}
            sourceMeta={sourceMeta}
            onUpdate={handleArrayUpdate}
            editedFields={editedFields}
          />
        </ReviewSection>
      </div>

      {saveError && (
        <div className="flex items-start gap-2 text-sm text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded-lg">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{saveError}</span>
        </div>
      )}

      <div className="flex items-center justify-between pt-2 border-t border-gray-200">
        <button
          type="button"
          onClick={onCancel}
          disabled={saving}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
        >
          Cancel
        </button>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => handleSave(false)}
            disabled={saving}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <CheckCircle className="w-4 h-4" />
            )}
            Save to Library
          </button>
          <button
            type="button"
            onClick={() => handleSave(true)}
            disabled={saving}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary bg-primary/10 border border-primary/30 rounded-lg hover:bg-primary/20 disabled:opacity-50 transition-colors"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <CheckCircle className="w-4 h-4" />
            )}
            Save & Open in Studio
          </button>
        </div>
      </div>
    </div>
  );
}
