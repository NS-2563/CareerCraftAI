import { apiClient } from "@/lib/api";

const careerApi = {
  generateCareerReport(data) {
    return apiClient.post("/career-coach", data);
  },

  generateRoadmap(data) {
    return apiClient.post("/career-roadmap", data);
  },
};

export default careerApi;