import { QuestionProvider } from "@/interview/services/providers/QuestionProvider";
import { localQuestions } from "@/interview/services/data/questions/localQuestions";

export class LocalQuestionProvider extends QuestionProvider {
  async loadQuestions() {
    return localQuestions;
  }
}


