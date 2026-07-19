import { QuestionLoader } from "@/interview/services/QuestionLoader";
import { LocalQuestionProvider } from "@/interview/services/providers/LocalQuestionProvider";
import { CloudQuestionProvider } from "@/interview/services/providers/CloudQuestionProvider";
import { SessionEngine } from "@/interview/services/SessionEngine";

export function buildEngine() {
  const questionLoader = new QuestionLoader({
    providers: [new LocalQuestionProvider(), new CloudQuestionProvider()],
  });

  return new SessionEngine({ questionLoader });
}


