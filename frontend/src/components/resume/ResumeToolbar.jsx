import ExportMenu from "./export/ExportMenu";
import ResumeSaveButton from "./ResumeSaveButton";
import FinishResumeButton from "./FinishResumeButton";

export default function ResumeToolbar({ previewRef }) {

  return (
    <div className="flex items-center justify-between border-b px-6 py-4">

      <h1 className="text-2xl font-bold">
        Resume Studio
      </h1>

      <div className="flex gap-3">
        <ResumeSaveButton />
        <FinishResumeButton />
        <ExportMenu previewRef={previewRef} />
      </div>

    </div>
  );
}