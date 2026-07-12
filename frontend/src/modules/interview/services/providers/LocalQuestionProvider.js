import { QuestionProvider } from "@/modules/interview/services/providers/QuestionProvider";
import { localQuestions } from "@/modules/interview/services/data/questions/localQuestions";

export class LocalQuestionProvider extends QuestionProvider {
  async loadQuestions() {
    return localQuestions;
  }
}


