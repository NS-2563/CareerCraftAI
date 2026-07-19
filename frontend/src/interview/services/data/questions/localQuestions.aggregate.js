import { hrQuestions } from "./hrQuestions.js";
import { aptitudeQuestions } from "./aptitudeQuestions.js";
import { technicalQuestions } from "./technicalQuestions.js";
import { behavioralQuestions } from "./behavioralQuestions.js";
import { communicationQuestions } from "./communicationQuestions.js";


// Aggregate bank for LocalQuestionProvider.
export const localQuestions = [
  ...hrQuestions,
  ...aptitudeQuestions,
  ...technicalQuestions,
  ...behavioralQuestions,
  ...communicationQuestions,
];

