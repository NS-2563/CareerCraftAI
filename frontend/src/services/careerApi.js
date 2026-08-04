import { apiClient } from "@/lib/api";

const careerApi = {
  generateCareerReport(data) {
    return apiClient.post("/api/career-coach", data);
  },

  getSkillGapSummary() {
    return apiClient.get("/api/career/skill-gap-summary");
  },

  /**
   * Re-run roadmap generation using the user's current data.
   * @returns {Promise}  Resolves with the newly generated report.
   */
  refreshRoadmap() {
    return apiClient.post("/api/career/roadmap/refresh");
  },

  /**
   * Fetch one roadmap task's user-set status.
   * @param {number} taskId
   */
  getTaskStatus(taskId) {
    return apiClient.get(`/api/career/roadmap/tasks/${taskId}/status`);
  },

  /**
   * Set a roadmap task's status.
   * @param {number} taskId
   * @param {string} status  "not_started" | "in_progress" | "done"
   */
  setTaskStatus(taskId, status) {
    return apiClient.put(`/api/career/roadmap/tasks/${taskId}/status`, { status });
  },
};

export default careerApi;

