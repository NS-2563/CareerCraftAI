import { useQuery } from "@tanstack/react-query";

import { getJob } from "../api/jobTrackerApi";

export function useJob(jobId, options = {}) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJob(jobId),
    enabled: jobId !== undefined && jobId !== null,
    ...options,
  });
}

