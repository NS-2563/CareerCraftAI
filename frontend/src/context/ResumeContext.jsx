import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiClient } from "@/lib/api";
import { mapResumeFromBackend } from "@/utils/resumeDataCompat";
import { loadResume } from "@/services/resumeApi";

import { ResumeContext } from "./ResumeContext.store";
import { useAuth } from "./useAuth";

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
      
      const params = new URLSearchParams(window.location.search);
      const id = params.get("id");
      const parsed = id ? Number(id) : null;
      
      return parsed;
    } catch {
      return null;
    }
  })();

  const [resumeId, setResumeId] = useState(resumeIdFromUrl);
  const [resumeData, setResumeData] = useState(getInitialState);
  const [selectedTemplate, setSelectedTemplate] = useState(getStoredTemplate);

  useEffect(() => {
    // ResumeProvider is not allowed to use react-router hooks.
    // If the querystring changes without a full navigation, this won't auto-sync.
    queueMicrotask(() => {
      setResumeId(() => {
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

  const getBlankForSection = useCallback((section) => {
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
  }, []);

  const ensureSectionInitialized = useCallback((data, section, factory, minItems = 1) => {
    const arr = data?.[section];
    if (!Array.isArray(arr) || arr.length < minItems) {
      return {
        ...data,
        [section]: Array.from({ length: minItems }, () => factory()),
      };
    }
    return data;
  }, []);

  const ensureAllRepeatableSectionsInitialized = useCallback((data) => {
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
  }, [ensureSectionInitialized, getBlankForSection]);





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

  const addItem = useCallback((section, itemData) => {
    setResumeData((prev) => ({
      ...prev,
      [section]: [
        ...(prev?.[section] ?? []),
        itemData !== undefined
          ? itemData
          : section === "skills"
            ? { name: "", category: "" }
            : getBlankForSection(section),
      ],
    }));
  }, [getBlankForSection]);

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

  const createResumeOnBackend = useCallback(async () => {
    

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

    

    const newResume = response.data;

    setResumeId(() => {
      return newResume.id;
    });

    

    // Persist the created resume id in the URL so refresh/revisit rehydrates the same record.
    // This must happen immediately after successful creation (no page reload).
    if (newResume?.id) {
      const nextUrl = `/resume-studio?id=${newResume.id}`;
      
      window.history.replaceState({}, "", nextUrl);
      
    }

    const mapped = mapResumeFromBackend(newResume);

    if (mapped) {
      setResumeData(ensureAllRepeatableSectionsInitialized(mapped));
    }

    

    return newResume.id;
  }, [ensureAllRepeatableSectionsInitialized]);
  // Explicit new-resume entrypoint, triggered only by user actions
  // (Create Resume, Import Resume, Duplicate Resume, "New" button).
  // Never invoked automatically on page load.
  const newResumeInFlightRef = useRef(false);
  const startNewResume = useCallback(() => {
    // Guard duplicate POSTs from React StrictMode double-invocation or rapid
    // repeated clicks while a creation request is still in flight.
    if (newResumeInFlightRef.current) {
      return Promise.resolve(null);
    }
    newResumeInFlightRef.current = true;

    return createResumeOnBackend()
      .then((createdId) => {
        return createdId;
      })
      .finally(() => {
        newResumeInFlightRef.current = false;
      });
  }, [createResumeOnBackend]);


  function clearResume() {
    

    try {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(TEMPLATE_STORAGE_KEY);
    } catch {
      // Ignore errors
    }
    setResumeData(initialResume);
    setSelectedTemplate("modern");

    setResumeId(() => {
      return null;
    });

    
  }



  const loadedResumeIdRef = useRef(null);
  const { isLoading: authLoading } = useAuth();

  useEffect(() => {
    if (authLoading) return;
    if (!resumeId || loadedResumeIdRef.current === resumeId) return;

    loadedResumeIdRef.current = resumeId;

    loadResume(resumeId)
      .then((res) => {
        const mapped = mapResumeFromBackend(res);
        if (mapped) {
          setResumeData(ensureAllRepeatableSectionsInitialized(mapped));
        }
      })
      .catch(() => {
        loadedResumeIdRef.current = null;
      });
  }, [resumeId, authLoading, ensureAllRepeatableSectionsInitialized]);

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
    [resumeData, selectedTemplate, resumeId, addItem, startNewResume]
  );


  return <ResumeContext.Provider value={value}>{children}</ResumeContext.Provider>;
}



