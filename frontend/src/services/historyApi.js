import { apiClient } from "@/lib/api";

const historyApi = {
  getHistory() {
    return apiClient.get("/career/history");
  },

  getReport(id) {
    return apiClient.get(`/career/history/${id}`);
  },

  deleteReport(id) {
    return apiClient.delete(`/career/history/${id}`);
  },

  clearHistory() {
    return apiClient.delete("/career/history");
  },
};

export default historyApi;

