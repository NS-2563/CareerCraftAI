import { apiClient } from "@/lib/api";
import { normalizeError } from "@/utils/apiErrorHandler";

// Backend uses /api/cover-letter
const API_BASE = "/api/cover-letter";



// CRUD Operations
export async function createCoverLetter(coverLetterData, signal) {
  try {
    const response = await apiClient.post(API_BASE, coverLetterData, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("createCoverLetter API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

export async function getCoverLetter(coverLetterId, signal) {
  try {
    const response = await apiClient.get(`${API_BASE}/${coverLetterId}`, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("getCoverLetter API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

export async function listCoverLetters(resumeId = null, signal) {
  try {
    const params = resumeId ? { resume_id: resumeId } : {};
    const response = await apiClient.get(API_BASE, { params, signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("listCoverLetters API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

export async function updateCoverLetter(coverLetterId, coverLetterData, signal) {
  try {
    const response = await apiClient.put(`${API_BASE}/${coverLetterId}`, coverLetterData, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("updateCoverLetter API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

export async function deleteCoverLetter(coverLetterId, signal) {
  try {
    await apiClient.delete(`${API_BASE}/${coverLetterId}`, { signal });
    return { success: true, data: { message: "Cover letter deleted" } };
  } catch (error) {
    console.error("deleteCoverLetter API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

export async function duplicateCoverLetter(coverLetterId, newTitle, signal) {
  try {
    const response = await apiClient.post(
      `${API_BASE}/${coverLetterId}/duplicate`,
      { title: newTitle },
      { signal }
    );
    return { success: true, data: response.data };
  } catch (error) {
    console.error("duplicateCoverLetter API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

export async function renameCoverLetter(coverLetterId, newTitle, signal) {
  try {
    const response = await apiClient.post(
      `${API_BASE}/${coverLetterId}/rename`,
      { title: newTitle },
      { signal }
    );
    return { success: true, data: response.data };
  } catch (error) {
    console.error("renameCoverLetter API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

// Version History
export async function getVersionHistory(coverLetterId, signal) {
  try {
    const response = await apiClient.get(`${API_BASE}/${coverLetterId}/versions`, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("getVersionHistory API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

export async function restoreVersion(coverLetterId, version, signal) {
  try {
    const response = await apiClient.post(
      `${API_BASE}/${coverLetterId}/restore`,
      { version },
      { signal }
    );
    return { success: true, data: response.data };
  } catch (error) {
    console.error("restoreVersion API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

// Archive
export async function archiveCoverLetter(coverLetterId, signal) {
  try {
    const response = await apiClient.post(`${API_BASE}/${coverLetterId}/archive`, {}, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("archiveCoverLetter API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

export async function restoreCoverLetter(coverLetterId, signal) {
  try {
    const response = await apiClient.post(`${API_BASE}/${coverLetterId}/restore`, {}, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("restoreCoverLetter API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

// Search
export async function searchCoverLetters(query, includeArchived = false, sort = "updated_at", signal) {
  try {
    const params = { include_archived: includeArchived, sort };
    if (query && query.trim()) params.q = query.trim();
    const response = await apiClient.get(`${API_BASE}/search`, { params, signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("searchCoverLetters API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

// Archived list
export async function listArchivedCoverLetters(signal) {
  try {
    const response = await apiClient.get(`${API_BASE}/archived/list`, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("listArchivedCoverLetters API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

// Deterministic pre-flight check: which required inputs are missing
export async function preflightCoverLetter(request, signal) {
  try {
    const response = await apiClient.post(`${API_BASE}/preflight`, request, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("preflightCoverLetter API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

// ATS keyword coverage (deterministic, computed from stored JD + content)
export async function getAtsCoverage(coverLetterId, signal) {
  try {
    const response = await apiClient.get(`${API_BASE}/${coverLetterId}/ats-coverage`, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("getAtsCoverage API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

// Deterministic before/after diff between two versions of a letter
export async function getCoverLetterDiff(coverLetterId, fromVersion, toVersion, signal) {
  try {
    const response = await apiClient.get(`${API_BASE}/${coverLetterId}/diff`, {
      params: { from_version: fromVersion, to_version: toVersion },
      signal,
    });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("getCoverLetterDiff API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

// AI Generation
export async function generateCoverLetter(request, signal) {
  try {
    const response = await apiClient.post(`${API_BASE}/generate`, request, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("generateCoverLetter API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

export async function generateCoverLetterForExisting(coverLetterId, request, signal) {
  try {
    const response = await apiClient.post(
      `${API_BASE}/${coverLetterId}/generate`,
      request,
      { signal }
    );
    return { success: true, data: response.data };
  } catch (error) {
    console.error("generateCoverLetterForExisting API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

// AI Editing
export async function editCoverLetter(coverLetterId, request, signal) {
  try {
    const response = await apiClient.post(
      `${API_BASE}/${coverLetterId}/edit`,
      request,
      { signal }
    );
    return { success: true, data: response.data };
  } catch (error) {
    console.error("editCoverLetter API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

export async function applyEditCoverLetter(coverLetterId, request, signal) {
  try {
    const response = await apiClient.post(
      `${API_BASE}/${coverLetterId}/apply-edit`,
      request,
      { signal }
    );
    return { success: true, data: response.data };
  } catch (error) {
    console.error("applyEditCoverLetter API error:", error);
    return { success: false, error: normalizeError(error).message };
  }
}

