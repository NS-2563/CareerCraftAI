import { shuffleArray } from "@/modules/interview/services/utils/random";

/**
 * @typedef {Object} QuestionLoaderFilters
 * @property {string=} category
 * @property {string=} topic
 * @property {string=} difficulty
 */

/**
 * Loads questions from all providers, merges, deduplicates,
 * filters, randomizes, and returns the requested number.
 */
export class QuestionLoader {
  /**
   * @param {Object} deps
   * @param {Array<{loadQuestions: Function}>} deps.providers
   */
  constructor({ providers }) {
    if (!Array.isArray(providers) || providers.length === 0) {
      throw new Error("QuestionLoader requires at least one provider");
    }

    this.providers = providers;
  }

  /**
   * @param {QuestionLoaderFilters} filters
   * @param {number} count
   * @returns {Promise<Array>}
   */
  async loadQuestions(filters = {}, count) {
    const requested =
      typeof count === "number" && count > 0 ? count : 0;

    if (!requested) {
      return [];
    }

    // Load questions from every provider
    const providerResults = await Promise.all(
      this.providers.map((provider) => provider.loadQuestions(filters))
    );

    // Merge all provider results
    const merged = providerResults.flat();

    // Remove duplicate question IDs
    const seen = new Set();
    const deduped = [];

    for (const question of merged) {
      if (!question?.id) continue;

      if (seen.has(question.id)) {
        continue;
      }

      seen.add(question.id);
      deduped.push(question);
    }

    const { category, topic, difficulty } = filters;

    const normCategory =
      category != null ? String(category).trim().toLowerCase() : undefined;

    const normTopic =
      topic != null ? String(topic).trim().toLowerCase() : undefined;

    const normDifficulty =
      difficulty != null
        ? String(difficulty).trim().toLowerCase()
        : undefined;

    // Apply filters
    const filtered = deduped.filter((question) => {
      if (
        normCategory &&
        String(question.category ?? "").trim().toLowerCase() !== normCategory
      ) {
        return false;
      }

      if (
        normTopic &&
        String(question.topic ?? "").trim().toLowerCase() !== normTopic
      ) {
        return false;
      }

      if (
        normDifficulty &&
        String(question.difficulty ?? "").trim().toLowerCase() !==
          normDifficulty
      ) {
        return false;
      }

      return true;
    });

    // Shuffle and return requested amount
    return shuffleArray(filtered).slice(0, requested);
  }
}