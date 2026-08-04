import { apiClient } from "@/lib/api";

const API_BASE = "/api/interview-prep/sessions";

export async function createSession(data) {
  const { data: responseData } = await apiClient.post(API_BASE, data);
  return responseData;
}

export async function updateSession(sessionId, data) {
  const { data: responseData } = await apiClient.put(`${API_BASE}/${sessionId}`, data);
  return responseData;
}

export async function listSessions({ page = 1, pageSize = 10 } = {}) {
  const { data: responseData } = await apiClient.get(API_BASE, {
    params: { page, page_size: pageSize },
  });
  return responseData;
}

export async function getSession(sessionId) {
  const { data: responseData } = await apiClient.get(`${API_BASE}/${sessionId}`);
  return responseData;
}

export async function createRealInterview(data) {
  const { data: responseData } = await apiClient.post(
    "/api/interview-prep/real-interviews",
    data,
  );
  return responseData;
}

export async function listRealInterviews(jobApplicationId) {
  const { data: responseData } = await apiClient.get(
    `/api/interview-prep/applications/${jobApplicationId}/real-interviews`,
  );
  return responseData;
}

export async function listApplicationSessions(jobApplicationId) {
  const { data: responseData } = await apiClient.get(
    `/api/interview-prep/applications/${jobApplicationId}/sessions`,
  );
  return responseData;
}

const interviewSessionApi = {
  createSession,
  updateSession,
  listSessions,
  getSession,
  createRealInterview,
  listRealInterviews,
  listApplicationSessions,
};

export default interviewSessionApi;
