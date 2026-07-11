export const STORAGE_KEY = "careercraft_resume";
export const TEMPLATE_STORAGE_KEY = "careercraft_resume_template";

export const initialResume = {
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

export function getStoredTemplate() {
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

export function getInitialState() {
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

export function getBlankForSection(section) {
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

export function ensureSectionInitialized(data, section, factory, minItems = 1) {
  const arr = data?.[section];
  if (!Array.isArray(arr) || arr.length < minItems) {
    return {
      ...data,
      [section]: Array.from({ length: minItems }, () => factory()),
    };
  }
  return data;
}

export function ensureAllRepeatableSectionsInitialized(data) {
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
