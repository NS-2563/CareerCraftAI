import { createContext, useMemo, useState, useCallback } from "react";

import { buildEngine } from "@/modules/interview/context/interviewEngine";
import { PRACTICE_MODE, SESSION_STATUS } from "@/modules/interview/services/constants/interviewConstants";

export const InterviewContext = createContext(null);

export function InterviewProvider({ children }) {
  const engine = useMemo(() => buildEngine(), []);

  const [currentSession, setCurrentSession] = useState(null);
  const [questionBank, setQuestionBank] = useState([]);

  const currentQuestion = useMemo(() => {
    if (!currentSession?.currentQuestionId) return null;
    return questionBank.find((q) => q.id === currentSession.currentQuestionId) || null;
  }, [currentSession, questionBank]);

  const createSession = useCallback(
    async ({
      // Phase 2 config (wizard)
      interviewMode,
      difficulty,
      questionCount,
      // timerMode/interviewType/company/jobRole/notes are stored as session metadata only
      timerMode,
      interviewType,
      company,
      jobRole,
      notes,

      // Backwards-compatible parameters
      mode = interviewType ?? PRACTICE_MODE.PRACTICE,
      filters = {},
    } = {}) => {
      // Map wizard selection into QuestionLoader filters (category/difficulty)
      const mappedFilters = {
        ...filters,
      };

      // interviewMode -> category
      const modeToCategory = {
        hr: "HR",
        technical: "Technical",
        aptitude: "Aptitude",
        behavioral: "Behavioral",
        communication: "Communication",
      };

      if (interviewMode && interviewMode !== "mixed") {
        mappedFilters.category = modeToCategory[interviewMode] ?? mappedFilters.category;
      } else {
        delete mappedFilters.category;
      }

      // difficulty -> canonical difficulty values in local question data are:
      // "Easy" | "Medium" | "Hard".
      // SetupWizard emits lowercase: "easy" | "medium" | "hard".
      // Normalize here so QuestionLoader filtering doesn't eliminate everything.
      const difficultyToCanonical = {
        easy: "Easy",
        medium: "Medium",
        hard: "Hard",
      };

      if (difficulty && difficulty !== "mixed") {
        mappedFilters.difficulty = difficultyToCanonical[difficulty] ?? difficulty;
      } else {
        delete mappedFilters.difficulty;
      }

      const result = await engine.createSession({
        mode,
        questionCount,
        filters: mappedFilters,
        interviewMode,
        difficulty,
        timerMode,
        interviewType,
        company,
        jobRole,
        notes,
      });

      const { session, selectedQuestions } = result;

      setCurrentSession(session);

      // selectedQuestions come from the exact same selection used to build session.questionIds.
      setQuestionBank(selectedQuestions);

      return session;
    },
    [engine]
  );

  const startSession = useCallback(() => {
    setCurrentSession((s) => (s ? engine.startSession(s) : s));
  }, [engine]);

  const pauseSession = useCallback(() => {
    setCurrentSession((s) => (s ? engine.pauseSession(s) : s));
  }, [engine]);

  const resumeSession = useCallback(() => {
    setCurrentSession((s) => (s ? engine.resumeSession(s) : s));
  }, [engine]);

  const skipQuestion = useCallback(() => {
    setCurrentSession((s) => (s ? engine.skipQuestion(s) : s));
  }, [engine]);

  const submitAnswer = useCallback(
    ({ questionId, responseText } = {}) => {
      setCurrentSession((s) => {
        if (!s) return s;
        const answer = {
          questionId,
          answer: String(responseText ?? ""),
          skipped: false,
          answeredAt: Date.now(),
        };
        return engine.saveAnswer(s, answer);
      });
    },
    [engine]
  );

  const skipCurrentQuestion = useCallback(
    (answerText = "") => {
      console.log("skipCurrentQuestion called", answerText);

      setCurrentSession((s) => {
        console.log("Session before skip:", s);

        if (!s) return s;

        const qid = s.currentQuestionId;
        if (!qid) return s;

        const trimmed = answerText.trim();

        const sessionWithAnswer = trimmed
          ? engine.saveAnswer(s, {
              questionId: qid,
              answer: trimmed,
              skipped: false,
              answeredAt: Date.now(),
            })
          : engine.saveAnswer(s, {
              questionId: qid,
              answer: "",
              skipped: true,
              answeredAt: Date.now(),
            });

        console.log("Session after saveAnswer:", sessionWithAnswer);

        return engine.skipQuestion(sessionWithAnswer);
      });
    },
    [engine]
  );

  const finishSession = useCallback(() => {
    setCurrentSession((s) => (s ? engine.finishSession(s) : s));
  }, [engine]);

  const generateSummary = useCallback(() => {
    if (!currentSession) return null;
    return engine.generateSummary(currentSession, questionBank);
  }, [engine, currentSession, questionBank]);

  const value = useMemo(
    () => ({
      currentSession,
      currentQuestion,
      questionBank,
      sessionStatus: currentSession?.status ?? SESSION_STATUS.NOT_STARTED,
      navigation: {
        skipQuestion,
        skipCurrentQuestion,
        goToNextQuestion: () => {
          setCurrentSession((s) => (s ? engine.goToNextQuestion(s) : s));
        },
        goToPreviousQuestion: () => {
          setCurrentSession((s) => (s ? engine.goToPreviousQuestion(s) : s));
        },
      },
      session: {
        createSession,
        startSession,
        pauseSession,
        resumeSession,
        finishSession,
        submitAnswer,
        generateSummary,
      },
    }),
    [
      currentSession,
      currentQuestion,
      questionBank,
      skipQuestion,
      skipCurrentQuestion,
      createSession,
      startSession,
      pauseSession,
      resumeSession,
      finishSession,
      submitAnswer,
      generateSummary,
    ]
  );

  return <InterviewContext.Provider value={value}>{children}</InterviewContext.Provider>;
}




