import { apiClient } from "@/lib/api";

const dashboardApi = {
  getSummary() {
    return apiClient.get("/api/dashboard/summary");
  },
  getHealthScore() {
    return apiClient.get("/api/dashboard/health-score");
  },
  getMilestones() {
    return apiClient.get("/api/dashboard/milestones");
  },
};

export default dashboardApi;
