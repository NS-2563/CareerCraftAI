import { QuestionProvider } from "@/modules/interview/services/providers/QuestionProvider";
import interviewPrepApi from "@/modules/interview/services/interviewPrepApi";

function titleCase(str) {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

export class CloudQuestionProvider extends QuestionProvider {
  async loadQuestions(filters = {}) {
    const jobTitle = filters.job_title;
    if (!jobTitle) {
      return [];
    }

    try {
      const payload = {
        job_title: jobTitle,
        skills: filters.skills || [],
        difficulty: (filters.difficulty || "medium").toLowerCase(),
        question_count: 5,
      };

      const data = await interviewPrepApi.generateQuestions(payload);
      const questions = data.questions || [];

      if (questions.length === 0) {
        return [];
      }

      return questions.map((q, i) => ({
        id: q.id || `ai-q-${Date.now()}-${i}`,
        prompt: q.question,
        category: titleCase(q.category) || "Technical",
        topic: q.topic || "",
        difficulty: titleCase(q.difficulty) || "Medium",
      }));
    } catch {
      return [];
    }
  }
}
