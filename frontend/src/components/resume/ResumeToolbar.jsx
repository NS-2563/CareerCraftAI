import ExportMenu from "./export/ExportMenu";
import ResumeSaveButton from "./ResumeSaveButton";
import FinishResumeButton from "./FinishResumeButton";

export default function ResumeToolbar({ previewRef }) {

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b px-4 sm:px-6 py-4">

      <h1 className="text-xl sm:text-2xl font-bold">
        Resume Studio
      </h1>

      <div className="flex flex-wrap gap-2 w-full sm:w-auto">
        <ResumeSaveButton />
        <FinishResumeButton />
        <ExportMenu previewRef={previewRef} />
      </div>

    </div>
  );
}

