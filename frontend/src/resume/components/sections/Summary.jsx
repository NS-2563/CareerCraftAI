import { Sparkles, Loader2 } from "lucide-react";
import FormSection from "@/components/common/FormSection";
import { Textarea } from "@/components/ui/textarea";
import { useResumeContext } from "@/resume/context/useResumeContext";
import useAI from "@/hooks/useAI";
import { generateSummary } from "@/services/aiService";

export default function Summary() {
  const { loading, execute } = useAI();
  const { resumeData, updateField } = useResumeContext();

  const summary = resumeData.summary || "";
  const personal = resumeData.personal || {};
  async function handleGenerateSummary() {
    const result = await execute(generateSummary, personal);

    if (result) {
      updateField("summary", null, result);
    }
  }

  return (
    <FormSection title="Summary">
      <div className="space-y-2">
        <div className="flex justify-end">
          <button
            onClick={handleGenerateSummary}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg border hover:bg-muted disabled:opacity-50 transition-colors"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            <span>Generate with AI</span>
          </button>
        </div>

        <Textarea
          value={summary || ""}
          onChange={(e) =>
            updateField("summary", null, e.target.value)
          }
          placeholder="Write a professional summary..."
          rows={6}
        />
      </div>
    </FormSection>
  );
}

