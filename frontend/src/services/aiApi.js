import { apiClient } from "@/lib/api";
import { USE_MOCK_AI } from "@/config/environment";

const API_BASE = "/api/ai";

export async function generateSummary(personal, signal) {
  if (USE_MOCK_AI) {
    const { generateSummary: mockFn } = await import("./aiService");
    return mockFn(personal);
  }

  try {
    // Map personal object to backend fields
    const payload = {
      first_name: personal?.first_name,
      last_name: personal?.last_name,
      email: personal?.email,
      phone: personal?.phone,
      location: personal?.location,
    };
    const response = await apiClient.post(
      `${API_BASE}/generate-summary`,
      payload,
      { signal }
    );
    return { success: true, data: response.data.summary };
  } catch (error) {
    if (error.name === "CanceledError" || error.code === "ECONNABORTED") {
      throw error;
    }
    console.error("generateSummary API error:", error);
    return { success: false, error: error.message };
  }
}

export async function improveSummary(currentSummary, signal) {
  if (USE_MOCK_AI) {
    const { improveSummary: mockFn } = await import("./aiService");
    return mockFn(currentSummary);
  }

  try {
    // Backend expects { text } not { summary }
    const response = await apiClient.post(
      `${API_BASE}/improve-summary`,
      { text: currentSummary },
      { signal }
    );
    // Backend returns { improved_text }
    return { success: true, data: response.data.improved_text };
  } catch (error) {
    if (error.name === "CanceledError" || error.code === "ECONNABORTED") {
      throw error;
    }
    console.error("improveSummary API error:", error);
    return { success: false, error: error.message };
  }
}

export async function improveExperience(experience, signal) {
  if (USE_MOCK_AI) {
    const { improveExperience: mockFn } = await import("./aiService");
    return mockFn(experience);
  }

  try {
    // Backend expects { text, position?, company? }
    const response = await apiClient.post(
      `${API_BASE}/improve-experience`,
      { text: experience },
      { signal }
    );
    return { success: true, data: response.data.improved_text };
  } catch (error) {
    if (error.name === "CanceledError" || error.code === "ECONNABORTED") {
      throw error;
    }
    console.error("improveExperience API error:", error);
    return { success: false, error: error.message };
  }
}

export async function improveProject(project, signal) {
  if (USE_MOCK_AI) {
    const { improveProject: mockFn } = await import("./aiService");
    return mockFn(project);
  }

  try {
    // Backend expects { text, name? }
    const response = await apiClient.post(
      `${API_BASE}/improve-project`,
      { text: project },
      { signal }
    );
    return { success: true, data: response.data.improved_text };
  } catch (error) {
    if (error.name === "CanceledError" || error.code === "ECONNABORTED") {
      throw error;
    }
    console.error("improveProject API error:", error);
    return { success: false, error: error.message };
  }
}

export async function suggestSkills(currentSkills, signal) {
  if (USE_MOCK_AI) {
    const { suggestSkills: mockFn } = await import("./aiService");
    return mockFn(currentSkills);
  }

  try {
    // Backend expects { current_skills?, job_title?, job_description? }
    const response = await apiClient.post(
      `${API_BASE}/suggest-skills`,
      { current_skills: currentSkills || [] },
      { signal }
    );
    return { success: true, data: response.data.skills };
  } catch (error) {
    if (error.name === "CanceledError" || error.code === "ECONNABORTED") {
      throw error;
    }
    console.error("suggestSkills API error:", error);
    return { success: false, error: error.message };
  }
}

export async function analyzeResume(resumeData, signal) {
  if (USE_MOCK_AI) {
    const { analyzeResume: mockFn } = await import("./aiService");
    return mockFn(resumeData);
  }

  try {
    const response = await apiClient.post(
      `${API_BASE}/analyze-resume`,
      { resume: resumeData },
      { signal }
    );
    return {
      success: true,
      data: {
        resumeScore: response.data.resume_score,
        atsScore: response.data.ats_score,
        suggestions: response.data.suggestions,
        strengths: response.data.strengths,
        weaknesses: response.data.weaknesses,
      },
    };
  } catch (error) {
    if (error.name === "CanceledError" || error.code === "ECONNABORTED") {
      throw error;
    }
    console.error("analyzeResume API error:", error);
    return { success: false, error: error.message };
  }
}

export default {
  generateSummary,
  improveSummary,
  improveExperience,
  improveProject,
  suggestSkills,
  analyzeResume,
};

