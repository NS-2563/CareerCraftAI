/**
 * Abstraction for loading questions.
 *
 * Providers must be framework-agnostic.
 */

export class QuestionProvider {
  /**
   * @param {Object} filters
   * @param {string=} filters.category
   * @param {string=} filters.topic
   * @param {string=} filters.difficulty
   * @returns {Promise<Array<{id:string,prompt:string,category?:string,topic?:string,difficulty?:string}>>}
   */
  async loadQuestions() {
    throw new Error("QuestionProvider.loadQuestions() not implemented");
  }
}



