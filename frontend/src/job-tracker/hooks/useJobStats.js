import { useQuery } from "@tanstack/react-query";

import { getJobStats } from "../api/jobTrackerApi";

export function useJobStats() {
  return useQuery({
    queryKey: ["jobStats"],
    queryFn: getJobStats,
  });
}

