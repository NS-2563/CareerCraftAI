import { apiClient } from "@/lib/api";

const activityApi = {
  /**
   * Fetch the full chronological activity feed (newest-first).
   *
   * @param {object} params
   * @param {string=} params.eventType          Filter to one event type.
   * @param {number|string=} params.jobApplicationId  Filter to one job application.
   * @param {number=} params.limit              Max items per request (default 200).
   * @param {number=} params.offset             Pagination offset.
   */
  getFeed({ eventType, jobApplicationId, limit = 200, offset = 0 } = {}) {
    return apiClient.get("/api/activity", {
      params: {
        event_type: eventType || undefined,
        job_application_id: jobApplicationId || undefined,
        limit,
        offset,
      },
    });
  },

  getRecent(limit = 10) {
    return apiClient.get("/api/activity/recent", { params: { limit } });
  },
};

export default activityApi;
