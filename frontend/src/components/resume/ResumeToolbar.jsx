import { useNavigate } from "react-router-dom";
import { BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import ExportMenu from "./export/ExportMenu";
import ResumeSaveButton from "./ResumeSaveButton";
import FinishResumeButton from "./FinishResumeButton";
import { useResumeContext } from "@/context/useResumeContext";

export default function ResumeToolbar({ previewRef }) {
  const navigate = useNavigate();
  const { resumeId } = useResumeContext();

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b px-4 sm:px-6 py-4">

      <h1 className="text-xl sm:text-2xl font-bold">
        Resume Studio
      </h1>

      <div className="flex flex-wrap gap-2 w-full sm:w-auto">
        {resumeId && (
          <Button variant="outline" size="sm" onClick={() => navigate(`/resume?id=${resumeId}`)}>
            <BarChart3 className="w-4 h-4 mr-1" />
            Analyze
          </Button>
        )}
        <ResumeSaveButton />
        <FinishResumeButton />
        <ExportMenu previewRef={previewRef} />
      </div>

    </div>
  );
}

