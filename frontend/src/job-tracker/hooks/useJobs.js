import { useQuery } from "@tanstack/react-query";

import { getJobs } from "../api/jobTrackerApi";

export function useJobs(params = {}) {
  return useQuery({
    queryKey: ["jobs", params],
    queryFn: () => getJobs(params),
  });
}

