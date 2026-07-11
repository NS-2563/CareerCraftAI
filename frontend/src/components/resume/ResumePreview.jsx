import { forwardRef } from "react";
import { templates } from "./templates";
import { useResumeContext } from "@/context/ResumeContext";

const ResumePreview = forwardRef(function ResumePreview(_, ref) {
  const { resumeData, selectedTemplate } = useResumeContext();
  const Template = templates[selectedTemplate] || templates.modern;

  if (!resumeData) {
    return <div ref={ref}>No data</div>;
  }

  return (
    <div ref={ref} style={{ minHeight: "1120px" }}>
      <Template resumeData={resumeData} />
    </div>
  );
});

export default ResumePreview;