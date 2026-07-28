import { apiClient } from "@/lib/api";

const API_BASE = "/api/communication";

export async function getMessages(params = {}) {
  const { data } = await apiClient.get(API_BASE, { params });
  return data;
}

export async function getMessage(id) {
  const { data } = await apiClient.get(`${API_BASE}/${id}`);
  return data;
}

export async function createMessage(data) {
  const { data: responseData } = await apiClient.post(API_BASE, data);
  return responseData;
}

export async function generateMessage(data) {
  const { data: responseData } = await apiClient.post(`${API_BASE}/generate`, data);
  return responseData;
}

export async function updateMessage(id, data) {
  const { data: responseData } = await apiClient.put(`${API_BASE}/${id}`, data);
  return responseData;
}

export async function deleteMessage(id) {
  const { data } = await apiClient.delete(`${API_BASE}/${id}`);
  return data;
}

export async function duplicateMessage(id, data) {
  const { data: responseData } = await apiClient.post(`${API_BASE}/${id}/duplicate`, data);
  return responseData;
}

export async function renameMessage(id, data) {
  const { data: responseData } = await apiClient.post(`${API_BASE}/${id}/rename`, data);
  return responseData;
}

export async function archiveMessage(id) {
  const { data: responseData } = await apiClient.post(`${API_BASE}/${id}/archive`);
  return responseData;
}

export async function restoreMessage(id) {
  const { data: responseData } = await apiClient.post(`${API_BASE}/${id}/restore`);
  return responseData;
}

export async function getMessageVersions(id) {
  const { data } = await apiClient.get(`${API_BASE}/${id}/versions`);
  return data;
}

export async function restoreMessageVersion(id, data) {
  const { data: responseData } = await apiClient.post(`${API_BASE}/${id}/restore-version`, data);
  return responseData;
}

// Suggestions API
export async function getSuggestions() {
  const { data } = await apiClient.get(`${API_BASE}/suggestions`);
  return data;
}

export async function dismissSuggestion(id) {
  const { data } = await apiClient.post(`${API_BASE}/suggestions/${id}/dismiss`);
  return data;
}

export async function generateFromSuggestion(id) {
  const { data } = await apiClient.post(`${API_BASE}/suggestions/${id}/generate`);
  return data;
}

const communicationApi = {
  getMessages,
  getMessage,
  createMessage,
  generateMessage,
  updateMessage,
  deleteMessage,
  duplicateMessage,
  renameMessage,
  archiveMessage,
  restoreMessage,
  getMessageVersions,
  restoreMessageVersion,
  getSuggestions,
  dismissSuggestion,
  generateFromSuggestion,
};

export default communicationApi;
