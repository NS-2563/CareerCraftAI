import { useQuery } from "@tanstack/react-query";

import { listRealInterviews } from "@/modules/interview/services/interviewSessionApi";

/**
 * Real-interview logs tied to a specific job application.
 */
export function useRealInterviews(jobApplicationId, options = {}) {
  return useQuery({
    queryKey: ["realInterviewsForJob", jobApplicationId],
    queryFn: async () => {
      const result = await listRealInterviews(jobApplicationId);
      return Array.isArray(result) ? result : [];
    },
    enabled: jobApplicationId !== undefined && jobApplicationId !== null,
    retry: false,
    ...options,
  });
}
