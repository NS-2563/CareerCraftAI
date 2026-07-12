import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, Check, AlertCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useResumeContext } from "@/context/useResumeContext";
import { updateResume } from "@/services/resumeApi";
import { mapResumePayloadForFinishBackend } from "@/utils/resumeFinishDataCompat";

export default function FinishResumeButton({ disabled }) {
  const { resumeId, resumeData } = useResumeContext();
  const navigate = useNavigate();

  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  async function handleFinish() {
    setError(null);
    setStatus("saving");

    if (!resumeId) {
      setError("Resume not initialized yet.");
      setStatus(null);
      return;
    }

    try {
      const payload = mapResumePayloadForFinishBackend(resumeData);

      const finishPayload = {
        ...payload,
        completed: true,
      };

      await updateResume(resumeId, finishPayload);

      setStatus("saved");

      navigate("/");
    } catch (err) {
      setError(err?.message || "Finish failed");
      setStatus(null);
    }
  }

  return (
    <div className="flex items-center gap-2">
      <Button
        type="button"
        onClick={handleFinish}
        disabled={disabled || !resumeId || status === "saving"}
      >
        {status === "saving" ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="ml-2">Finishing...</span>
          </>
        ) : (
          <>
            <Check className="w-4 h-4" />
            <span className="ml-2">Finish Resume</span>
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

