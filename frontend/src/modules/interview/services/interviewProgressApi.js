import { apiClient } from "@/lib/api";

const API_BASE = "/api/interview-prep/progress";

export async function getProgress(sort = "score_asc") {
  const { data: responseData } = await apiClient.get(API_BASE, {
    params: { sort },
  });
  return responseData;
}

const interviewProgressApi = {
  getProgress,
};

export default interviewProgressApi;
