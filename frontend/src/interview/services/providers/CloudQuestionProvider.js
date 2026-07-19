import { QuestionProvider } from "@/interview/services/providers/QuestionProvider";

/**
 * Stub provider.
 * Will be replaced with backend API later.
 */
export class CloudQuestionProvider extends QuestionProvider {
  async loadQuestions() {
    return [];
  }
}