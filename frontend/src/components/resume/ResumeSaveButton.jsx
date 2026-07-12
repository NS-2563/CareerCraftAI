import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, Save, AlertCircle } from "lucide-react";
import { updateResume } from "@/services/resumeApi";
import { mapResumePayloadForBackend } from "@/utils/resumeDataCompat";
import { useResumeContext } from "@/context/useResumeContext";

export default function ResumeSaveButton({ disabled }) {
  const { resumeId, resumeData } = useResumeContext();

  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  const payload = useMemo(() => {
    return mapResumePayloadForBackend(resumeData);
  }, [resumeData]);

  async function handleSave() {
    setError(null);
    setStatus("saving");

    if (!resumeId) {
      setError("Resume not initialized yet.");
      setStatus(null);
      return;
    }

    try {
      await updateResume(resumeId, payload);

      setStatus("saved");

      setTimeout(() => setStatus(null), 1200);
    } catch (err) {
      setError(err?.message || "Save failed");
      setStatus(null);
    }
  }

  return (
    <div className="flex items-center gap-2">
      <Button
        type="button"
        onClick={handleSave}
        disabled={disabled || !resumeId || status === "saving"}
      >
        {status === "saving" ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="ml-2">Saving...</span>
          </>
        ) : (
          <>
            <Save className="w-4 h-4" />
            <span className="ml-2">
              {status === "saved" ? "Saved" : "Save"}
            </span>
          </>
        )}
      </Button>

      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded-lg">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

