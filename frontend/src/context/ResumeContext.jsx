import { createContext, useEffect, useMemo, useRef, useState } from "react";
import { apiClient } from "@/lib/api";
import { mapResumeFromBackend } from "@/utils/resumeDataCompat";

import { ResumeContext } from "./ResumeContext.store";

const STORAGE_KEY = "careercraft_resume";
const TEMPLATE_STORAGE_KEY = "careercraft_resume_template";

function getStoredTemplate() {
  try {
    const stored = localStorage.getItem(TEMPLATE_STORAGE_KEY);
    if (stored && ["modern", "minimal", "professional", "corporate", "creative"].includes(stored)) {
      return stored;
    }
  } catch {
    // Ignore errors
  }
  return "modern";
}

const initialResume = {
  personal: {
    firstName: "",
    lastName: "",
    title: "",
    email: "",
    phone: "",
    location: "",
    linkedin: "",
    github: "",
    portfolio: "",
  },

  summary: "",

  experience: [],

  // Important: do not force-inject Education globally for all code paths.
  // Education is ensured only for newly created/empty resumes (see init helpers below).
  education: [],

  skills: [
    {
      name: "",
      category: "",
    },
  ],

  projects: [
    {
      title: "",
      techStack: "",
      github: "",
      liveDemo: "",
      description: "",
    },
  ],

  certifications: [
    {
      name: "",
      issuer: "",
      issueDate: "",
      credentialUrl: "",
    },
  ],

  languages: [
    {
      language: "",
      proficiency: "",
    },
  ],

  interests: [
    {
      name: "",
    },
  ],

  references: [
    {
      name: "",
      designation: "",
      organization: "",
      email: "",
      phone: "",
    },
  ],
};

function getInitialState() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch {
    // Ignore errors
  }
  return initialResume;
}

export function ResumeProvider({ children }) {
  const resumeIdFromUrl = (() => {
    try {
      console.log("[ResumeContext] resumeIdFromUrl BEFORE parsing", {
        search: window.location.search,
      });
      const params = new URLSearchParams(window.location.search);
      const id = params.get("id");
      const parsed = id ? Number(id) : null;
      console.log("[ResumeContext] resumeIdFromUrl AFTER parsing", {
        idRaw: id,
        parsed,
        pathname: window.location.pathname,
      });
      return parsed;
    } catch (e) {
      console.log("[ResumeContext] resumeIdFromUrl parse failed", {
        error: String(e),
        search: window.location.search,
      });
      return null;
    }
  })();

  const [resumeId, setResumeId] = useState(resumeIdFromUrl);
  const [resumeData, setResumeData] = useState(getInitialState);
  const [selectedTemplate, setSelectedTemplate] = useState(getStoredTemplate);

  // Instrumentation: log every resumeId change transition.
  useEffect(() => {
    console.log("[ResumeContext] resumeId CHANGE", {
      previous: undefined,
      current: resumeId,
      functionName: "useEffect(resumeId watcher)",
      reason: "resumeId state updated",
    });
  }, [resumeId]);


  useEffect(() => {
    // ResumeProvider is not allowed to use react-router hooks.
    // If the querystring changes without a full navigation, this won't auto-sync.
    queueMicrotask(() => {
      setResumeId((prev) => {
        console.log("[ResumeContext] setResumeId URL sync", {
          resumeIdBefore: prev,
          resumeIdAfter: resumeIdFromUrl,
          functionName: "URL sync effect",
          reason: "sync from resumeIdFromUrl (query param id)",
        });
        return resumeIdFromUrl;
      });
    });
  }, [resumeIdFromUrl]);



  useEffect(() => {
    // Keep local storage for editor draft continuity between refreshes.
    // Backend is used for actual resume persistence via Save.
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(resumeData));
    } catch {
      // Ignore storage errors
    }
  }, [resumeData]);

  useEffect(() => {
  console.log("[ResumeContext] resumeData UPDATED", resumeData);
}, [resumeData]);


  function ensureSectionInitialized(data, section, factory, minItems = 1) {
    const arr = data?.[section];
    if (!Array.isArray(arr) || arr.length < minItems) {
      return {
        ...data,
        [section]: Array.from({ length: minItems }, () => factory()),
      };
    }
    return data;
  }

  function ensureAllRepeatableSectionsInitialized(data) {
    let next = data;

    const factories = {
      experience: () => getBlankForSection("experience"),
      education: () => getBlankForSection("education"),
      skills: () => ({ name: "", category: "" }),
      projects: () => getBlankForSection("projects"),
      certifications: () => getBlankForSection("certifications"),
      languages: () => getBlankForSection("languages"),
      interests: () => getBlankForSection("interests"),
      references: () => getBlankForSection("references"),
    };

    Object.keys(factories).forEach((section) => {
      next = ensureSectionInitialized(next, section, factories[section], 1);
    });

    return next;
  }





  useEffect(() => {
    try {
      localStorage.setItem(TEMPLATE_STORAGE_KEY, selectedTemplate);
    } catch {
      // Ignore storage errors
    }
  }, [selectedTemplate]);

  function updateField(section, field, value) {
    setResumeData((prev) => {
      const prevSectionValue = prev?.[section];

      if (
        field === undefined ||
        field === null ||
        prevSectionValue === null ||
        prevSectionValue === undefined ||
        typeof prevSectionValue !== "object" ||
        Array.isArray(prevSectionValue)
      ) {
        return {
          ...prev,
          [section]: value,
        };
      }

      return {
        ...prev,
        [section]: {
          ...(prev?.[section] ?? {}),
          [field]: value,
        },
      };
    });
  }

  function getBlankForSection(section) {
    if (section === "experience") {
      return {
        company: "",
        position: "",
        location: "",
        startDate: "",
        endDate: "",
        current: false,
        description: "",
      };
    }

    if (section === "education") {
      return {
        institution: "",
        degree: "",
        fieldOfStudy: "",
        location: "",
        startDate: "",
        endDate: "",
        current: false,
        gpa: "",
        description: "",
      };
    }

    if (section === "projects") {
      return {
        title: "",
        techStack: "",
        github: "",
        liveDemo: "",
        description: "",
      };
    }

    if (section === "certifications") {
      return {
        name: "",
        issuer: "",
        issueDate: "",
        credentialUrl: "",
      };
    }

    if (section === "languages") {
      return {
        language: "",
        proficiency: "",
      };
    }

    if (section === "interests") {
      return {
        name: "",
      };
    }

    if (section === "references") {
      return {
        name: "",
        designation: "",
        organization: "",
        email: "",
        phone: "",
      };
    }

    return {};
  }

 function addItem(section) {
  setResumeData((prev) => ({
    ...prev,
    [section]: [
      ...(prev?.[section] ?? []),
      section === "skills"
        ? { name: "", category: "" }
        : getBlankForSection(section),
    ],
  }));
}

  function removeItem(section, index) {
    setResumeData((prev) => ({
      ...prev,
      [section]: (prev?.[section] ?? []).filter((_, i) => i !== index),
    }));
  }

  function updateArrayItem(section, index, data) {
    setResumeData((prev) => ({
      ...prev,
      [section]: (prev?.[section] ?? []).map((item, i) => (i === index ? data : item)),
    }));
  }

  async function createResumeOnBackend() {
    console.log("[ResumeContext] createResumeOnBackend ENTER", {
      resumeIdStateAtEntry: resumeId,
      url: window.location.href,
    });

    const response = await apiClient.post(`/api/resume`, {
      name: "Untitled Resume",
      personal: {},
      summary: "",
      experience: [],
      education: [],
      skills: [],
      projects: [],
      certifications: [],
      languages: [],
      interests: [],
      references: [],
    });

    console.log("[ResumeContext] createResumeOnBackend BACKEND RESPONSE RECEIVED", {
      status: response?.status,
      hasData: Boolean(response?.data),
    });

    const newResume = response.data;
    console.log("[ResumeContext] createResumeOnBackend newResume.id", {
      newResumeId: newResume?.id,
    });

    console.log("[ResumeContext] createResumeOnBackend BEFORE setResumeId", {
      currentResumeIdState: resumeId,
      newResumeId: newResume?.id,
    });

    setResumeId((prev) => {
      console.log("[ResumeContext] createResumeOnBackend setResumeId updater", {
        resumeIdBefore: prev,
        resumeIdAfter: newResume?.id ?? null,
        functionName: "createResumeOnBackend",
        reason: "POST /api/resume returned newResume.id",
      });
      return newResume.id;
    });

    console.log("[ResumeContext] createResumeOnBackend AFTER setResumeId (sync log, state update async)", {
      expectedNewResumeId: newResume?.id,
    });

    // Persist the created resume id in the URL so refresh/revisit rehydrates the same record.
    // This must happen immediately after successful creation (no page reload).
    if (newResume?.id) {
      const nextUrl = `/resume-studio?id=${newResume.id}`;
      console.log("[ResumeContext] createResumeOnBackend BEFORE URL update", {
        nextUrl,
        currentUrl: window.location.href,
      });
      window.history.replaceState({}, "", nextUrl);
      console.log("[ResumeContext] createResumeOnBackend AFTER URL update", {
        nextUrl,
        updatedUrl: window.location.href,
      });
    }

    const mapped = mapResumeFromBackend(newResume);

    if (mapped) {
      setResumeData(ensureAllRepeatableSectionsInitialized(mapped));
    }

    console.log("[ResumeContext] createResumeOnBackend EXIT", {
      createdId: newResume?.id,
      resumeIdStateAtExit: resumeId,
    });

    return newResume.id;
  }

  // Explicit new-resume entrypoint.
  // Idempotent + StrictMode-safe: will POST at most once until resumeId is set.
  const newResumeInFlightRef = useRef(false);
  function startNewResume() {
    console.log("[ResumeContext] startNewResume ENTER", {
      resumeIdStateAtEntry: resumeId,
      url: window.location.href,
      newResumeInFlightRefCurrent: newResumeInFlightRef.current,
    });

    // sessionStorage guard to prevent cross-remount duplicates.
    const guardKey = "careercraft_new_resume_guard_v1";

    // Inspect key existence/value BEFORE any guard decisions.
    let sessionGuardRaw = null;
    let sessionGuardExists = false;
    try {
      sessionGuardRaw = sessionStorage.getItem(guardKey);
      sessionGuardExists = sessionGuardRaw !== null;
    } catch (e) {
      console.log("[ResumeContext] startNewResume sessionStorage READ failed", {
        guardKey,
        error: String(e),
      });
    }

    const sessionGuardActive = sessionGuardRaw === "1";

    console.log("[ResumeContext] startNewResume session guard inspection", {
      guardKey,
      sessionGuardExists,
      sessionGuardRaw,
      sessionGuardActive,
      whereWritten: "startNewResume (setItem call)",
      whereCleared: "clearResume (not clearing this key by design during this flow)",
    });

    // If we already have a resumeId, do nothing.
    if (resumeId) {
      console.log("[ResumeContext] startNewResume EARLY RETURN guard=resumeId", {
        resumeId,
      });
      return Promise.resolve(resumeId);
    }

    // Guard duplicate POSTs due to React StrictMode remount.
    if (newResumeInFlightRef.current) {
      console.log("[ResumeContext] startNewResume EARLY RETURN guard=inFlight", {
        newResumeInFlightRefCurrent: newResumeInFlightRef.current,
      });
      return Promise.resolve(null);
    }
    newResumeInFlightRef.current = true;

    // ---- Minimal fix + strict requirement enforcement ----
    // The sessionStorage guard must only activate AFTER a successful resume creation.
    // We implement that by only treating the guard as active when the key is present
    // AND resumeId is non-null in this runtime.
    // Since this is the *first* call and resumeId is null, sessionGuardActive is ignored.
    // Duplicate calls are still blocked via newResumeInFlightRef.
    const guarded = sessionGuardActive && Boolean(resumeId);

    console.log("[ResumeContext] startNewResume guard evaluation", {
      resumeId,
      newResumeInFlightRefCurrent: newResumeInFlightRef.current,
      sessionGuardActive,
      guardedAfterFix: guarded,
    });

    if (guarded) {
      console.log("[ResumeContext] startNewResume EARLY RETURN guard=sessionStorage(allowed after success only)", {
        guardKey,
        sessionGuardRaw,
      });
      return Promise.resolve(null);
    }

    // Set the key ONLY after we successfully create the resume (moved out of the pre-guard path).
    // This prevents it from blocking the first ever POST.

    return createResumeOnBackend()
      .then((createdId) => {
        console.log("[ResumeContext] startNewResume createdId from createResumeOnBackend", {
          createdId,
          willWriteSessionGuardKey: Boolean(createdId),
          guardKey,
        });
        if (createdId) {
          try {
            sessionStorage.setItem(guardKey, "1");
            console.log("[ResumeContext] startNewResume session guard WRITTEN", {
              guardKey,
              value: sessionStorage.getItem(guardKey),
              where: "after successful createResumeOnBackend",
            });
          } catch (e) {
            console.log("[ResumeContext] startNewResume sessionStorage setItem failed", {
              guardKey,
              error: String(e),
            });
          }
        }
        return createdId;
      })
      .finally(() => {
        newResumeInFlightRef.current = false;
        console.log("[ResumeContext] startNewResume finally: inFlight cleared");
      });
  }




  function clearResume() {
    console.log("[ResumeContext] clearResume ENTER", {
      resumeIdStateAtEntry: resumeId,
      url: window.location.href,
    });

    try {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(TEMPLATE_STORAGE_KEY);
    } catch {
      // Ignore errors
    }
    setResumeData(initialResume);
    setSelectedTemplate("modern");

    setResumeId((prev) => {
      console.log("[ResumeContext] setResumeId NULL from clearResume", {
        resumeIdBefore: prev,
        resumeIdAfter: null,
        functionName: "clearResume",
        reason: "clearResume invoked",
      });
      return null;
    });

    console.log("[ResumeContext] clearResume EXIT", {
      resumeIdStateAtExit: resumeId,
    });
  }



  const value = useMemo(
    () => ({
      resumeData,
      setResumeData,
      updateField,
      addItem,
      removeItem,
      updateArrayItem,
      clearResume,
      selectedTemplate,
      setSelectedTemplate,
      resumeId,
      setResumeId,
      startNewResume,
    }),
    [resumeData, selectedTemplate, resumeId]
  );


  return <ResumeContext.Provider value={value}>{children}</ResumeContext.Provider>;
}



