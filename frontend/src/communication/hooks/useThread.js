import { useQuery } from "@tanstack/react-query";

import { getThread } from "../services/communicationApi";

export function useThread(jobApplicationId, options = {}) {
  return useQuery({
    queryKey: ["communicationThread", jobApplicationId],
    queryFn: () => getThread(jobApplicationId),
    enabled: jobApplicationId !== undefined && jobApplicationId !== null,
    retry: false,
    ...options,
  });
}
