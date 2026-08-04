import { useMemo, useState, useCallback, useRef, useEffect } from "react";

import { evaluateAnswer as evaluateAnswerApi } from "@/modules/interview/services/interviewPrepApi";
import * as sessionApi from "@/modules/interview/services/interviewSessionApi";
import { buildEngine } from "@/modules/interview/context/interviewEngine";
import { PRACTICE_MODE, SESSION_STATUS } from "@/modules/interview/services/constants/interviewConstants";
import { InterviewContext } from "./InterviewContext.store";

export function InterviewProvider({ children }) {
  const engine = useMemo(() => buildEngine(), []);

  const [currentSession, setCurrentSession] = useState(null);
  const [questionBank, setQuestionBank] = useState([]);
  const [evaluationsCache] = useState({});
  const persistIdRef = useRef(null);
  const sessionRef = useRef(null);

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

      // AI question generation fields
      jobTitle,
      skills,

      // Backwards-compatible parameters
      mode = interviewType ?? PRACTICE_MODE.PRACTICE,
      filters = {},
    } = {}) => {
      // Map wizard selection into QuestionLoader filters (category/difficulty)
      const mappedFilters = {
        ...filters,
      };

      // Pass AI-specific fields through to CloudQuestionProvider
      if (jobTitle) {
        mappedFilters.job_title = jobTitle;
      }
      if (skills?.length) {
        mappedFilters.skills = skills;
      }

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
      setQuestionBank(selectedQuestions);

      try {
        const persisted = await sessionApi.createSession({
          job_title: jobTitle ?? null,
          skills: skills?.length ? skills : null,
          difficulty: difficulty ?? null,
          question_count: questionCount,
          questions: selectedQuestions.map((q) => ({
            id: q.id,
            question: q.prompt ?? q.question ?? "",
            category: q.category ?? "",
            topic: q.topic ?? null,
            difficulty: q.difficulty ?? "",
          })),
          related_job_application_id: null,
        });
        if (persisted?.id) {
          persistIdRef.current = persisted.id;
        }
      } catch {
        // Persistence failure is non-fatal; session works in-memory
      }

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
      

      setCurrentSession((s) => {
        

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

        

        return engine.skipQuestion(sessionWithAnswer);
      });
    },
    [engine]
  );

  const finishSession = useCallback(() => {
    setCurrentSession((s) => (s ? engine.finishSession(s) : s));
  }, [engine]);

  useEffect(() => {
    sessionRef.current = currentSession;
  }, [currentSession]);

  const generateSummary = useCallback(() => {
    if (!currentSession) return null;
    return engine.generateSummary(currentSession, questionBank);
  }, [engine, currentSession, questionBank]);

  const evaluateAnswer = useCallback(
    async (questionId, answerText, jobTitle, difficulty) => {
      if (!questionId || !answerText?.trim()) return;

      try {
        const result = await evaluateAnswerApi({
          question: currentQuestion?.prompt ?? "",
          answer: answerText,
          job_title: jobTitle ?? null,
          difficulty: difficulty ?? null,
        });

        const evaluation = {
          questionId,
          ...result.evaluation,
          evaluation_failed: result.evaluation_failed ?? false,
        };

        setCurrentSession((s) =>
          s ? engine.saveEvaluation(s, evaluation) : s
        );
      } catch {
        // Silently fail — evaluation is best-effort
      }
    },
    [engine, currentQuestion]
  );

  const persistSessionUpdate = useCallback(
    async (overrides = {}) => {
      const pid = persistIdRef.current;
      if (!pid) return;

      const session = sessionRef.current;
      if (!session) return;

      const answersPayload = session.questionIds.map((qid) => {
        const answer = session.answers?.find((a) => a.questionId === qid) ?? null;
        const evaluation = session.evaluations?.find((e) => e.questionId === qid) ?? null;
        return {
          questionId: qid,
          answer: answer?.answer ?? "",
          skipped: answer?.skipped ?? false,
          answeredAt: answer?.answeredAt ?? null,
          evaluation: evaluation
            ? {
                score: evaluation.score ?? 0,
                strengths: evaluation.strengths ?? [],
                improvements: evaluation.improvements ?? [],
                model_answer_notes: evaluation.model_answer_notes ?? null,
                evaluation_failed: evaluation.evaluation_failed ?? false,
              }
            : null,
        };
      });

      const payload = { answers: answersPayload };
      if (overrides.overall_score != null) payload.overall_score = overrides.overall_score;
      if (overrides.completed_at) payload.completed_at = overrides.completed_at;

      try {
        await sessionApi.updateSession(pid, payload);
      } catch {
        // Best-effort
      }
    },
    []
  );

  const value = useMemo(
    () => ({
      currentSession,
      currentQuestion,
      questionBank,
      evaluationsCache,
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
        evaluateAnswer,
        persistSessionUpdate,
      },
    }),
    [
      currentSession,
      currentQuestion,
      questionBank,
      evaluationsCache,
      skipQuestion,
      skipCurrentQuestion,
      createSession,
      startSession,
      pauseSession,
      resumeSession,
      finishSession,
      submitAnswer,
      generateSummary,
      evaluateAnswer,
      persistSessionUpdate,
      engine,
    ]
  );

  return <InterviewContext.Provider value={value}>{children}</InterviewContext.Provider>;
}




