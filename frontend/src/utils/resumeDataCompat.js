// Compatibility helpers between backend resume schema (snake_case) and
// frontend ResumeContext schema (camelCase / different field names).

const isNonNullObject = (v) => v !== null && typeof v === "object";

function safeString(v) {
  if (v === undefined || v === null) return "";
  return String(v);
}

function mapPersonalFromBackend(personal) {
  const p = isNonNullObject(personal) ? personal : {};
  return {
    firstName: safeString(p.first_name),
    lastName: safeString(p.last_name),
    title: safeString(p.title),
    email: safeString(p.email),
    phone: safeString(p.phone),
    location: safeString(p.location),
    linkedin: safeString(p.linkedin),
    github: safeString(p.github),
    portfolio: safeString(p.website || ""),
  };
}

function mapExperienceFromBackend(experience) {
  if (!Array.isArray(experience)) return [];
  return experience.map((e) => {
    const x = isNonNullObject(e) ? e : {};
    return {
      // Backend supports optional id/current.
      id: safeString(x.id) || undefined,
      company: safeString(x.company),
      position: safeString(x.position),
      location: safeString(x.location),
      startDate: safeString(x.start_date),
      endDate: safeString(x.end_date),
      current: Boolean(x.current),
      description: safeString(x.description),
    };
  });
}

function mapEducationFromBackend(education) {
  if (!Array.isArray(education)) return [];
  return education.map((ed) => {
    const e = isNonNullObject(ed) ? ed : {};
    return {
      id: safeString(e.id) || undefined,
      institution: safeString(e.institution),
      degree: safeString(e.degree),
      fieldOfStudy: safeString(e.field_of_study),
      location: safeString(e.location),
      startDate: safeString(e.start_date),
      endDate: safeString(e.end_date),
      current: Boolean(e.current),
      gpa: safeString(e.gpa),
      description: safeString(e.description),
    };
  });
}

function mapSkillsFromBackend(skills) {
  if (!Array.isArray(skills)) return [];
  return skills.map((s) => {
    const x = isNonNullObject(s) ? s : {};
    return {
      id: safeString(x.id) || undefined,
      name: safeString(x.name),
      level: safeString(x.level),
      category: safeString(x.category),
    };
  });
}

function mapProjectsFromBackend(projects) {
  if (!Array.isArray(projects)) return [];
  return projects.map((p) => {
    const x = isNonNullObject(p) ? p : {};
    return {
      id: safeString(x.id) || undefined,
      title: safeString(x.name),
      techStack: Array.isArray(x.technologies) ? x.technologies.join(", ") : safeString(x.technologies),
      github: safeString(x.url),
      liveDemo: safeString(x.live_url),
      description: safeString(x.description),
    };
  });
}

function mapCertificationsFromBackend(certs) {
  if (!Array.isArray(certs)) return [];
  return certs.map((c) => {
    const x = isNonNullObject(c) ? c : {};
    return {
      id: safeString(x.id) || undefined,
      name: safeString(x.name),
      issuer: safeString(x.issuer),
      issueDate: safeString(x.date),
      credentialUrl: safeString(x.url),
    };
  });
}

function mapLanguagesFromBackend(langs) {
  if (!Array.isArray(langs)) return [];
  return langs.map((l) => {
    const x = isNonNullObject(l) ? l : {};
    return {
      id: safeString(x.id) || undefined,
      language: safeString(x.language),
      proficiency: safeString(x.proficiency),
    };
  });
}

function mapInterestsFromBackend(interests) {
  if (!Array.isArray(interests)) return [];
  return interests.map((i) => {
    const x = isNonNullObject(i) ? i : {};
    return {
      id: safeString(x.id) || undefined,
      name: safeString(x.name),
    };
  });
}

function mapReferencesFromBackend(refs) {
  if (!Array.isArray(refs)) return [];
  return refs.map((r) => {
    const x = isNonNullObject(r) ? r : {};
    return {
      id: safeString(x.id) || undefined,
      name: safeString(x.name),
      designation: safeString(x.title),
      organization: safeString(x.company),
      email: safeString(x.email),
      phone: safeString(x.phone),
    };
  });
}

function mapResumeFromBackend(resume) {
  if (!resume || typeof resume !== "object") return null;

  return {
    personal: mapPersonalFromBackend(resume.personal),
    summary: safeString(resume.summary),
    experience: mapExperienceFromBackend(resume.experience),
    education: mapEducationFromBackend(resume.education),
    skills: mapSkillsFromBackend(resume.skills),
    projects: mapProjectsFromBackend(resume.projects),
    certifications: mapCertificationsFromBackend(resume.certifications),
    languages: mapLanguagesFromBackend(resume.languages),
    interests: mapInterestsFromBackend(resume.interests),
    references: mapReferencesFromBackend(resume.references),
  };
}

// Convert frontend resumeData -> backend ResumeUpdate payload.
// Backend expects snake_case for nested fields.
function toPersonalForBackend(personal) {
  const p = isNonNullObject(personal) ? personal : {};
  return {
    first_name: p.firstName || "",
    last_name: p.lastName || "",
    title: p.title || "",
    email: p.email || "",
    phone: p.phone || "",
    location: p.location || "",
    linkedin: p.linkedin || "",
    github: p.github || "",
    website: p.portfolio || "",
  };
}

function toExperienceForBackend(experience) {
  if (!Array.isArray(experience)) return [];
  return experience.map((x) => ({
    id: x?.id,
    company: x?.company,
    position: x?.position,
    location: x?.location,
    start_date: x?.startDate,
    end_date: x?.endDate,
    current: Boolean(x?.current),
    description: x?.description,
  }));
}

function toEducationForBackend(education) {
  if (!Array.isArray(education)) return [];
  return education.map((e) => ({
    id: e?.id,
    institution: e?.institution,
    degree: e?.degree,
    field_of_study: e?.fieldOfStudy,
    location: e?.location,
    start_date: e?.startDate,
    end_date: e?.endDate,
    current: Boolean(e?.current),
    gpa: e?.gpa,
    description: e?.description,
  }));
}

function toSkillsForBackend(skills) {
  if (!Array.isArray(skills)) return [];
  return skills.map((s) => ({
    id: s?.id,
    name: s?.name,
    level: s?.level,
    category: s?.category,
  }));
}

function toProjectsForBackend(projects) {
  if (!Array.isArray(projects)) return [];
  return projects.map((p) => ({
    id: p?.id,
    name: p?.title,
    description: p?.description,
    url: p?.github,
    live_url: p?.liveDemo || undefined,
    technologies: typeof p?.techStack === "string"
      ? p.techStack.split(",").map((t) => t.trim()).filter(Boolean)
      : Array.isArray(p?.techStack)
        ? p.techStack
        : undefined,
  }));
}

function toCertificationsForBackend(certs) {
  if (!Array.isArray(certs)) return [];
  return certs.map((c) => ({
    id: c?.id,
    name: c?.name,
    issuer: c?.issuer,
    date: c?.issueDate,
    url: c?.credentialUrl,
  }));
}

function toLanguagesForBackend(langs) {
  if (!Array.isArray(langs)) return [];
  return langs.map((l) => ({
    id: l?.id,
    language: l?.language,
    proficiency: l?.proficiency,
  }));
}

function toInterestsForBackend(interests) {
  if (!Array.isArray(interests)) return [];
  return interests.map((i) => ({
    id: i?.id,
    name: i?.name,
  }));
}

function toReferencesForBackend(refs) {
  if (!Array.isArray(refs)) return [];
  return refs.map((r) => ({
    id: r?.id,
    name: r?.name,
    title: r?.designation,
    company: r?.organization,
    email: r?.email,
    phone: r?.phone,
  }));
}

function mapResumePayloadForBackend(resumeData) {
  return {
    personal: toPersonalForBackend(resumeData.personal),
    summary: resumeData.summary,
    experience: toExperienceForBackend(resumeData.experience),
    education: toEducationForBackend(resumeData.education),
    skills: toSkillsForBackend(resumeData.skills),
    projects: toProjectsForBackend(resumeData.projects),
    certifications: toCertificationsForBackend(resumeData.certifications),
    languages: toLanguagesForBackend(resumeData.languages),
    interests: toInterestsForBackend(resumeData.interests),
    references: toReferencesForBackend(resumeData.references),
  };
}

export {
  mapResumeFromBackend,
  mapResumePayloadForBackend,
};



