import { apiClient } from "@/lib/api";

const API_BASE = "/api/analysis";

export async function analyzeResume(resumeData, enableAi = false, resumeId = null, signal) {
  try {
    const payload = { resume: resumeData, enable_ai: enableAi };
    if (resumeId != null) {
      payload.resume_id = resumeId;
    }
    const response = await apiClient.post(
      `${API_BASE}/analyze`,
      payload,
      { signal }
    );
    return { success: true, data: response.data };
  } catch (error) {
    if (error.name === "CanceledError" || error.code === "ECONNABORTED") {
      throw error;
    }
    console.error("analyzeResume API error:", error);
    return { success: false, error: error.response?.data?.detail || error.message };
  }
}

export async function getCachedAnalysis(resumeId, signal) {
  try {
    const response = await apiClient.get(
      `${API_BASE}/resume/${resumeId}/latest`,
      { signal }
    );
    return { success: true, data: response.data };
  } catch (error) {
    if (error.name === "CanceledError") throw error;
    console.error("getCachedAnalysis API error:", error);
    return { success: false, error: error.response?.data?.detail || error.message };
  }
}

export async function getStaleStatus(resumeId, signal) {
  try {
    const response = await apiClient.get(
      `${API_BASE}/resume/${resumeId}/stale`,
      { signal }
    );
    return { success: true, data: response.data };
  } catch (error) {
    if (error.name === "CanceledError") throw error;
    console.error("getStaleStatus API error:", error);
    return { success: false, error: error.response?.data?.detail || error.message };
  }
}

export async function getAnalysisById(analysisId, signal) {
  try {
    const response = await apiClient.get(
      `${API_BASE}/${analysisId}`,
      { signal }
    );
    return { success: true, data: response.data };
  } catch (error) {
    if (error.name === "CanceledError") throw error;
    console.error("getAnalysisById API error:", error);
    return { success: false, error: error.response?.data?.detail || error.message };
  }
}

export async function getAnalysisHistory(resumeId, limit = 20, signal) {
  try {
    const response = await apiClient.get(
      `${API_BASE}/resume/${resumeId}/history`,
      { params: { limit }, signal }
    );
    return { success: true, data: response.data };
  } catch (error) {
    if (error.name === "CanceledError") throw error;
    console.error("getAnalysisHistory API error:", error);
    return { success: false, error: error.response?.data?.detail || error.message };
  }
}

export async function getScoreHistory(resumeId, metricType = "ats_score", limit = 20, signal) {
  try {
    const response = await apiClient.get(
      `/api/resume/${resumeId}/score-history`,
      { params: { metric_type: metricType, limit }, signal }
    );
    return { success: true, data: response.data };
  } catch (error) {
    if (error.name === "CanceledError") throw error;
    console.error("getScoreHistory API error:", error);
    return { success: false, error: error.response?.data?.detail || error.message };
  }
}

export async function getScoreHistoryDiff(resumeId, fromSnapshotId, toSnapshotId, signal) {
  try {
    const response = await apiClient.get(
      `/api/resume/${resumeId}/score-history/diff`,
      { params: { from: fromSnapshotId, to: toSnapshotId }, signal }
    );
    return { success: true, data: response.data };
  } catch (error) {
    if (error.name === "CanceledError") throw error;
    console.error("getScoreHistoryDiff API error:", error);
    return { success: false, error: error.response?.data?.detail || error.message };
  }
}

export async function reAnalyzeResume(resumeId, enableAi = false, signal) {
  try {
    const response = await apiClient.post(
      `${API_BASE}/resume/${resumeId}/re-analyze`,
      { enable_ai: enableAi, force: true },
      { signal }
    );
    return { success: true, data: response.data };
  } catch (error) {
    if (error.name === "CanceledError") throw error;
    console.error("reAnalyzeResume API error:", error);
    return { success: false, error: error.response?.data?.detail || error.message };
  }
}

export default { analyzeResume, getCachedAnalysis, getStaleStatus, getAnalysisById, getAnalysisHistory, getScoreHistory, getScoreHistoryDiff, reAnalyzeResume };
