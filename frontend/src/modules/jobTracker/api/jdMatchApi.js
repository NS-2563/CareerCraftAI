import { apiClient } from "@/lib/api";

const API_BASE = "/api/jd-match";

/**
 * Fetch the latest persisted JD match result for a job application.
 * @param {number} jobApplicationId
 */
export async function getMatchResult(jobApplicationId) {
  const { data } = await apiClient.get(
    `${API_BASE}/results/${jobApplicationId}`
  );
  return data;
}

/**
 * Re-run matching against a saved application's job description + linked resume.
 * The backend persists the fresh result.
 * @param {number} jobId
 * @param {boolean} enableAi
 */
export async function analyzeSavedJob(jobId, enableAi = false) {
  const { data } = await apiClient.post(
    `${API_BASE}/analyze-saved/${jobId}?enable_ai=${enableAi}`
  );
  return data;
}

/**
 * Run an ad-hoc match (not linked to an application).
 */
export async function analyzeJob(matchRequest) {
  const { data } = await apiClient.post(`${API_BASE}/analyze`, matchRequest);
  return data;
}

const jdMatchApi = {
  getMatchResult,
  analyzeSavedJob,
  analyzeJob,
};

export default jdMatchApi;
