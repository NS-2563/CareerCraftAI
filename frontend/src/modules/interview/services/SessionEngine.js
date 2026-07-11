import {
  DEFAULT_QUESTION_COUNT,
  SESSION_STATUS,
  PRACTICE_MODE,
} from "@/modules/interview/services/constants/interviewConstants";

/**
 * Framework-independent session engine.
 * No React, no router, no timers, no scoring.
 */
export class SessionEngine {
  constructor({ questionLoader }) {
    if (!questionLoader) {
      throw new Error("SessionEngine requires questionLoader");
    }

    this.questionLoader = questionLoader;
  }

  async createSession({
    mode = PRACTICE_MODE.PRACTICE,
    questionCount = DEFAULT_QUESTION_COUNT,
    filters = {},

    interviewMode,
    difficulty,
    timerMode,
    interviewType,
    company,
    jobRole,
    notes,
  } = {}) {
    const selectedQuestions = await this.questionLoader.loadQuestions(
      filters,
      questionCount
    );

    const session = {
      sessionId: `sess_${Math.random().toString(16).slice(2)}_${Date.now()}`,

      mode,
      status: SESSION_STATUS.NOT_STARTED,

      currentQuestionId: selectedQuestions[0]?.id ?? null,
      questionIds: selectedQuestions.map((q) => q.id),

      createdAtEpochMs: Date.now(),
      answers: [],

      interviewMode,
      difficulty,
      questionCount,
      timerMode,
      interviewType,
      company,
      jobRole,
      notes,
    };

    return {
      session,
      selectedQuestions,
    };
  }

  startSession(session) {
    const next = this._cloneSession(session);

    if (next.status === SESSION_STATUS.NOT_STARTED) {
      next.status = SESSION_STATUS.IN_PROGRESS;
      next.startedAtEpochMs = Date.now();
    }

    return next;
  }

  pauseSession(session) {
    const next = this._cloneSession(session);

    if (next.status === SESSION_STATUS.IN_PROGRESS) {
      next.status = SESSION_STATUS.PAUSED;
    }

    return next;
  }

  resumeSession(session) {
    const next = this._cloneSession(session);

    if (next.status === SESSION_STATUS.PAUSED) {
      next.status = SESSION_STATUS.IN_PROGRESS;
    }

    return next;
  }

  submitAnswer(session, answer) {
    const next = this._cloneSession(session);

    if (!answer?.questionId) return next;

    if (next.status === SESSION_STATUS.NOT_STARTED) {
      next.status = SESSION_STATUS.IN_PROGRESS;
      next.startedAtEpochMs = Date.now();
    }

    const normalized = {
      questionId: answer.questionId,
      answer: answer.answer ?? answer.responseText ?? "",
      skipped: Boolean(answer.skipped),
      answeredAt:
        answer.answeredAt ??
        answer.submittedAtEpochMs ??
        Date.now(),
    };

    const index = next.answers.findIndex(
      (a) => a.questionId === normalized.questionId
    );

    if (index >= 0) {
      next.answers[index] = normalized;
    } else {
      next.answers.push(normalized);
    }

    return next;
  }

  /**
   * Backward compatibility.
   */
  saveAnswer(session, answer) {
    return this.submitAnswer(session, answer);
  }

  getCurrentQuestion(session) {
    if (!session?.currentQuestionId) {
      return null;
    }

    return {
      currentQuestionId: session.currentQuestionId,
      currentIndex: session.questionIds.indexOf(
        session.currentQuestionId
      ),
    };
  }

  goToNextQuestion(session) {
    return this.skipQuestion(session);
  }

  goToPreviousQuestion(session) {
    const next = this._cloneSession(session);

    if (next.status === SESSION_STATUS.NOT_STARTED) {
      next.status = SESSION_STATUS.IN_PROGRESS;
      next.startedAtEpochMs = Date.now();
    }

    const currentIndex = next.currentQuestionId
      ? next.questionIds.indexOf(next.currentQuestionId)
      : -1;

    const previousIndex = currentIndex - 1;

    if (previousIndex >= 0) {
      next.currentQuestionId = next.questionIds[previousIndex];
    } else {
      next.currentQuestionId = next.questionIds[0] ?? null;
    }

    return next;
  }

  skipQuestion(session) {
    const next = this._cloneSession(session);

    if (next.status === SESSION_STATUS.NOT_STARTED) {
      next.status = SESSION_STATUS.IN_PROGRESS;
      next.startedAtEpochMs = Date.now();
    }

    const currentIndex = next.currentQuestionId
      ? next.questionIds.indexOf(next.currentQuestionId)
      : -1;

    const nextIndex = currentIndex + 1;

    if (nextIndex < next.questionIds.length) {
      next.currentQuestionId = next.questionIds[nextIndex];
    } else {
      next.status = SESSION_STATUS.FINISHED;
      next.finishedAtEpochMs = Date.now();
      next.currentQuestionId = null;
    }

    return next;
  }

  finishSession(session) {
    const next = this._cloneSession(session);

    next.status = SESSION_STATUS.FINISHED;
    next.finishedAtEpochMs = Date.now();
    next.currentQuestionId = null;

    return next;
  }

  generateSummary(session, questions = []) {
    const questionMap = new Map(
      questions.map((q) => [q.id, q])
    );

    const answerMap = new Map(
      session.answers.map((a) => [a.questionId, a])
    );

    return {
      sessionId: session.sessionId,
      mode: session.mode,
      status: session.status,
      createdAtEpochMs: session.createdAtEpochMs,
      startedAtEpochMs: session.startedAtEpochMs,
      finishedAtEpochMs: session.finishedAtEpochMs,

      questions: session.questionIds.map((id) => {
        const question = questionMap.get(id);
        const answer = answerMap.get(id);

        return {
          questionId: id,
          prompt: question?.prompt ?? "",
          answerText: answer?.answer ?? "",
          skipped: answer?.skipped ?? false,
          submittedAtEpochMs: answer?.answeredAt,
        };
      }),
    };
  }

  _cloneSession(session) {
    return {
      ...session,
      answers: Array.isArray(session.answers)
        ? session.answers.map((a) => ({ ...a }))
        : [],
    };
  }
}