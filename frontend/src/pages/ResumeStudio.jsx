import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

import ResumeBuilder from "@/components/resume/ResumeBuilder";
import { useResumeContext } from "@/context/useResumeContext";

export default function ResumeStudio() {
  const location = useLocation();
  const {
    resumeId,
    startNewResume,
  } = useResumeContext();

  const [initialSection, setInitialSection] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const id = params.get("id");
    const section = params.get("section");

    if (section) {
      setInitialSection(section);
    }

    // Explicit new-resume flow:
    // - if ?id is missing AND we don't already have a resumeId => create
    // - additionally support the legacy Create Resume entrypoint (?create=1)
    //   which should always initialize a new resume
    const createFlag = params.get("create");

    const shouldCreate = Boolean(createFlag) || (!id && !resumeId);
    if (shouldCreate && !resumeId) {
      startNewResume();
    }

  }, [location.search, resumeId, startNewResume]);

  return <ResumeBuilder initialSection={initialSection} />;
}




