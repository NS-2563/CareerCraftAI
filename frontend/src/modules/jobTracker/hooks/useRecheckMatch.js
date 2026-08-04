import { useMutation, useQueryClient } from "@tanstack/react-query";

import { analyzeSavedJob } from "../api/jdMatchApi";

export function useRecheckMatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ jobId, enableAi = false }) =>
      analyzeSavedJob(jobId, enableAi),
    onSuccess: (_data, variables) => {
      const jobId = variables?.jobId;
      queryClient.invalidateQueries({ queryKey: ["jdMatchResult", jobId] });
    },
  });
}
