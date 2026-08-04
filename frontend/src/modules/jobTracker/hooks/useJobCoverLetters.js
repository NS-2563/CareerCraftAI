import { useQuery } from "@tanstack/react-query";

import { listCoverLetters } from "@/services/coverLetterApi";

/**
 * Cover letters linked to a specific job application.
 */
export function useJobCoverLetters(jobApplicationId, options = {}) {
  return useQuery({
    queryKey: ["coverLettersForJob", jobApplicationId],
    queryFn: async () => {
      const result = await listCoverLetters(null);
      if (!result?.success) return [];
      const jobId = Number(jobApplicationId);
      return (result.data || []).filter((cl) => Number(cl.job_application_id) === jobId);
    },
    enabled: jobApplicationId !== undefined && jobApplicationId !== null,
    retry: false,
    ...options,
  });
}
