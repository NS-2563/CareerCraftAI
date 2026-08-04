import { useQuery } from "@tanstack/react-query";

import { getMatchResult } from "../api/jdMatchApi";

export function useJDMatchResult(jobApplicationId, options = {}) {
  return useQuery({
    queryKey: ["jdMatchResult", jobApplicationId],
    queryFn: () => getMatchResult(jobApplicationId),
    enabled:
      jobApplicationId !== undefined &&
      jobApplicationId !== null &&
      (options.enabled !== false),
    retry: false,
    ...options,
  });
}
