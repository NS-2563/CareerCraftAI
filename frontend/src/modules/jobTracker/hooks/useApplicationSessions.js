import { useQuery } from "@tanstack/react-query";

import { listApplicationSessions } from "@/modules/interview/services/interviewSessionApi";

/**
 * All interview sessions (practice + real-interview logs) tied to a job
 * application, oldest first — the interview-events source for the
 * per-application timeline.
 */
export function useApplicationSessions(jobApplicationId, options = {}) {
  return useQuery({
    queryKey: ["applicationSessions", jobApplicationId],
    queryFn: async () => {
      const result = await listApplicationSessions(jobApplicationId);
      return Array.isArray(result) ? result : [];
    },
    enabled: jobApplicationId !== undefined && jobApplicationId !== null,
    retry: false,
    ...options,
  });
}
