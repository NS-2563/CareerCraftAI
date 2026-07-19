import { useMutation, useQueryClient } from "@tanstack/react-query";

import { deleteJob } from "../api/jobTrackerApi";

export function useDeleteJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      queryClient.invalidateQueries({ queryKey: ["jobStats"] });
    },
  });
}

