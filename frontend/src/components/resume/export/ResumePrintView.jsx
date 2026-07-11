import { useMemo } from "react";
import useResume from "@/hooks/useResumes";
import { templates } from "../templates";

export default function ResumePrintView({ resumeData, selectedTemplate }) {
  const ctx = useResume?.();
  const templateKey = selectedTemplate || ctx?.selectedTemplate || "modern";

  const Template = templates[templateKey] || templates.modern;

  // Ensure we always render full resume UI from data.
  const data = useMemo(() => resumeData || ctx?.resumeData || {}, [resumeData, ctx?.resumeData]);

  return (
    <div
      className="print:bg-white print:text-black"
      style={{ width: "210mm", minHeight: "297mm", background: "white", color: "black" }}
    >
      <Template resumeData={data} />
    </div>
  );
}

