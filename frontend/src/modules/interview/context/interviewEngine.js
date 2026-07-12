import { QuestionLoader } from "@/modules/interview/services/QuestionLoader";
import { LocalQuestionProvider } from "@/modules/interview/services/providers/LocalQuestionProvider";
import { CloudQuestionProvider } from "@/modules/interview/services/providers/CloudQuestionProvider";
import { SessionEngine } from "@/modules/interview/services/SessionEngine";

export function buildEngine() {
  const questionLoader = new QuestionLoader({
    providers: [new LocalQuestionProvider(), new CloudQuestionProvider()],
  });

  return new SessionEngine({ questionLoader });
}


