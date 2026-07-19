import { apiClient } from "@/lib/api";
import { USE_MOCK_AI } from "@/config/environment";

const API_BASE = "/api/resume";

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));


/* ============================================================
   LIST
============================================================ */



export async function listResumes(archived = null) {
  const params = {};

  if (archived !== null) {
    params.archived = archived;
  }

  const { data } = await apiClient.get(API_BASE, { params });

  return data;
}



/* ============================================================
   LOAD
============================================================ */

export async function loadResume(id) {
  if (USE_MOCK_AI) {
    await delay(300);

    return {
      id,
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
    };
  }

  const { data } = await apiClient.get(`${API_BASE}/${id}`);
  return data;
}

/* ============================================================
   CREATE
============================================================ */

export async function saveResume(payload) {
  if (USE_MOCK_AI) {
    await delay(300);

    return {
      id: crypto.randomUUID(),
      ...payload,
    };
  }

  const { data } = await apiClient.post(API_BASE, payload);
  return data;
}

/* ============================================================
   UPDATE
============================================================ */

export async function updateResume(id, payload) {
  if (USE_MOCK_AI) {
    await delay(300);

    return {
      id,
      ...payload,
    };
  }

  const { data } = await apiClient.put(
    `${API_BASE}/${id}`,
    payload
  );

  return data;
}

/* ============================================================
   DELETE
============================================================ */

export async function deleteResume(id) {
  if (USE_MOCK_AI) {
    await delay(200);
    return { id };
  }

  await apiClient.delete(`${API_BASE}/${id}`);

  return { id };
}

/* ============================================================
   DUPLICATE
============================================================ */

export async function duplicateResume(id, name) {
  if (USE_MOCK_AI) {
    await delay(200);

    return {
      id: crypto.randomUUID(),
      name: "Copy of Resume",
    };
  }

  const { data } = await apiClient.post(
  `${API_BASE}/${id}/duplicate`,
  {
    name,
  }
);

  return data;
}

/* ============================================================
   RENAME
============================================================ */

export async function renameResume(id, name) {
  if (USE_MOCK_AI) {
    await delay(200);

    return {
      id,
      name,
    };
  }

  const { data } = await apiClient.post(
    `${API_BASE}/${id}/rename`,
    {
      name,
    }
  );

  return data;
}

/* ============================================================
   ARCHIVE
============================================================ */

export async function archiveResume(id) {
  const { data } = await apiClient.post(
    `${API_BASE}/${id}/archive`
  );

  return data;
}

/* ============================================================
   RESTORE
============================================================ */

export async function restoreResume(id) {
  const { data } = await apiClient.post(
    `${API_BASE}/${id}/restore`
  );

  return data;
}

/* ============================================================
   VERSION HISTORY
============================================================ */

export async function getVersions(id) {
  const { data } = await apiClient.get(
    `${API_BASE}/${id}/versions`
  );

  return data;
}

export async function restoreVersion(id, version) {
  const { data } = await apiClient.post(
    `${API_BASE}/${id}/restore-version`,
    { version }
  );

  return data;
}

/* ============================================================
   CANONICAL SERVICE
============================================================ */

export const resumeApi = {
  listResumes,
  loadResume,
  saveResume,
  updateResume,
  deleteResume,
  duplicateResume,
  renameResume,
  archiveResume,
  restoreResume,
  getVersions,
  restoreVersion,
};

export default resumeApi;

