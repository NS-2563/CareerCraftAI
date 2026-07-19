/**
 * Interview module data models (single source of truth)
 *
 * Note: This project uses JavaScript. Models are expressed as
 * JSDoc typedefs for documentation and editor support.
 */

/** @typedef {Object} Question
 *  @property {string} id
 *  @property {string} prompt
 *  @property {string=} category
 *  @property {string=} topic
 *  @property {string=} difficulty
 *  @property {string=} expectedAnswer
 */

/** @typedef {Object} Category
 *  @property {string} id
 *  @property {string} name
 */

/** @typedef {('practice'|'mock')} PracticeMode */

/** @typedef {('not_started'|'in_progress'|'paused'|'finished')} SessionStatus */

/**
 * A user's response to a question.
 *
 * skipped=true means the user intentionally skipped the question.
 * If answer contains text, skipped should always be false.
 */
 /**
  * @typedef {Object} SessionAnswer
  * @property {string} questionId
  * @property {string} answer
  * @property {boolean} skipped
  * @property {number} answeredAt
  */

/** @typedef {Object} InterviewSession
 *  @property {string} sessionId
 *  @property {PracticeMode} mode
 *  @property {SessionStatus} status
 *  @property {string=} currentQuestionId
 *  @property {string[]} questionIds
 *  @property {number} createdAtEpochMs
 *  @property {number=} startedAtEpochMs
 *  @property {number=} finishedAtEpochMs
 *  @property {SessionAnswer[]} answers
 *
 *  @property {('mixed'|string)=} interviewMode
 *  @property {('mixed'|string)=} difficulty
 *  @property {number=} questionCount
 *  @property {('off'|'per_question'|'entire_session'|string)=} timerMode
 *  @property {('practice'|'mock'|string)=} interviewType
 *  @property {string=} company
 *  @property {string=} jobRole
 *  @property {string=} notes
 */

export {};

