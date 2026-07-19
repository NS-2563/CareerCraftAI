import { useMutation, useQueryClient } from "@tanstack/react-query";

import { updateJob } from "../api/jobTrackerApi";

export function useUpdateJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => updateJob(id, data),
    onSuccess: (_updatedJob, variables) => {
      const jobId = variables?.id;

      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      queryClient.invalidateQueries({ queryKey: ["job", jobId] });
      queryClient.invalidateQueries({ queryKey: ["jobStats"] });
    },
  });
}

