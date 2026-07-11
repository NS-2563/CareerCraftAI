import { apiClient } from "@/lib/api";

// Backend uses /api/cover-letter
const API_BASE = "/api/cover-letter";



// CRUD Operations
export async function createCoverLetter(coverLetterData, signal) {
  try {
    const response = await apiClient.post(API_BASE, coverLetterData, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("createCoverLetter API error:", error);
    return { success: false, error: error.message };
  }
}

export async function getCoverLetter(coverLetterId, signal) {
  try {
    const response = await apiClient.get(`${API_BASE}/${coverLetterId}`, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("getCoverLetter API error:", error);
    return { success: false, error: error.message };
  }
}

export async function listCoverLetters(resumeId = null, signal) {
  try {
    const params = resumeId ? { resume_id: resumeId } : {};
    const response = await apiClient.get(API_BASE, { params, signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("listCoverLetters API error:", error);
    return { success: false, error: error.message };
  }
}

export async function updateCoverLetter(coverLetterId, coverLetterData, signal) {
  try {
    const response = await apiClient.put(`${API_BASE}/${coverLetterId}`, coverLetterData, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("updateCoverLetter API error:", error);
    return { success: false, error: error.message };
  }
}

export async function deleteCoverLetter(coverLetterId, signal) {
  try {
    await apiClient.delete(`${API_BASE}/${coverLetterId}`, { signal });
    return { success: true, data: { message: "Cover letter deleted" } };
  } catch (error) {
    console.error("deleteCoverLetter API error:", error);
    return { success: false, error: error.message };
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
    return { success: false, error: error.message };
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
    return { success: false, error: error.message };
  }
}

// Version History
export async function getVersionHistory(coverLetterId, signal) {
  try {
    const response = await apiClient.get(`${API_BASE}/${coverLetterId}/versions`, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("getVersionHistory API error:", error);
    return { success: false, error: error.message };
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
    return { success: false, error: error.message };
  }
}

// Archive
export async function archiveCoverLetter(coverLetterId, signal) {
  try {
    const response = await apiClient.post(`${API_BASE}/${coverLetterId}/archive`, {}, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("archiveCoverLetter API error:", error);
    return { success: false, error: error.message };
  }
}

export async function restoreCoverLetter(coverLetterId, signal) {
  try {
    const response = await apiClient.post(`${API_BASE}/${coverLetterId}/restore`, {}, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("restoreCoverLetter API error:", error);
    return { success: false, error: error.message };
  }
}

// Search
export async function searchCoverLetters(query, includeArchived = false, signal) {
  try {
    const response = await apiClient.get(`${API_BASE}/search`, {
      params: { q: query, include_archived: includeArchived },
      signal,
    });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("searchCoverLetters API error:", error);
    return { success: false, error: error.message };
  }
}

// AI Generation
export async function generateCoverLetter(request, signal) {
  try {
    const response = await apiClient.post(`${API_BASE}/generate`, request, { signal });
    return { success: true, data: response.data };
  } catch (error) {
    console.error("generateCoverLetter API error:", error);
    return { success: false, error: error.message };
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
    return { success: false, error: error.message };
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
    return { success: false, error: error.message };
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
    return { success: false, error: error.message };
  }
}