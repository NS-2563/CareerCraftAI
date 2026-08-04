import { apiClient } from "@/lib/api";

const API_BASE = "/api/interview-prep";

export async function generateQuestions(data) {
  const { data: responseData } = await apiClient.post(
    `${API_BASE}/generate-questions`,
    data,
  );
  return responseData;
}

export async function evaluateAnswer(data) {
  const { data: responseData } = await apiClient.post(
    `${API_BASE}/evaluate-answer`,
    data,
  );
  return responseData;
}

const interviewPrepApi = {
  generateQuestions,
  evaluateAnswer,
};

export default interviewPrepApi;
