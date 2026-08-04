import { apiClient } from "@/lib/api";

const analyticsApi = {
  getAnalytics() {
    return apiClient.get("/career/analytics");
  },

  /**
   * Fetch historical score snapshots for a metric.
   *
   * @param {string} metricType  Metric identifier (e.g. "ats_score", "career_readiness").
   * @param {number} [limit=100]  Max number of snapshots to return.
   * @param {boolean} [descending=false]  Return newest snapshots first.
   */
  getHistory(metricType, limit = 100, descending = false) {
    return apiClient.get("/api/analytics/history", {
      params: { metric_type: metricType, limit, descending },
    });
  },
};

export default analyticsApi;
