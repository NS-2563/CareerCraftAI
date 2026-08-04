import { apiClient } from "@/lib/api";

const API_BASE = "/api/jobs";

/**
 * Fetch all job applications for the authenticated user.
 *
 * @param {object} params
 * @param {string=} params.status
 * @param {string=} params.search
 * @param {string=} params.sort_by
 * @param {boolean=} params.descending
 */
export async function getJobs(params = {}) {
  const { data } = await apiClient.get(API_BASE, { params });
  return data;
}

/**
 * Fetch a single job application.
 * @param {number|string} id
 */
export async function getJob(id) {
  const { data } = await apiClient.get(`${API_BASE}/${id}`);
  return data;
}

/**
 * Create a new job application.
 * @param {object} data
 */
export async function createJob(data) {
  const { data: responseData } = await apiClient.post(API_BASE, data);
  return responseData;
}

/**
 * Update a job application.
 * @param {number|string} id
 * @param {object} data
 */
export async function updateJob(id, data) {
  const { data: responseData } = await apiClient.put(`${API_BASE}/${id}`, data);
  return responseData;
}

/**
 * Delete a job application.
 * @param {number|string} id
 */
export async function deleteJob(id) {
  const { data } = await apiClient.delete(`${API_BASE}/${id}`);
  return data;
}

/**
 * Fetch dashboard statistics.
 */
export async function getJobStats() {
  const { data } = await apiClient.get(`${API_BASE}/stats`);
  return data;
}

/**
 * Fetch the workspace header payload for an application: the deterministic
 * recommended next action plus the non-dismissed insight cards.
 * @param {number|string} jobId
 */
export async function getWorkspaceInsights(jobId) {
  const { data } = await apiClient.get(`${API_BASE}/${jobId}/workspace`);
  return data;
}

/**
 * Dismiss an insight card for an application so it does not reappear.
 * Returns the updated dismissed-keys list.
 * @param {number|string} jobId
 * @param {string} insightKey
 */
export async function dismissWorkspaceInsight(jobId, insightKey) {
  const { data } = await apiClient.post(
    `${API_BASE}/${jobId}/workspace/insights/${insightKey}/dismiss`
  );
  return data;
}

const jobTrackerApi = {
  getJobs,
  getJob,
  createJob,
  updateJob,
  deleteJob,
  getJobStats,
  getWorkspaceInsights,
  dismissWorkspaceInsight,
};

export default jobTrackerApi;

