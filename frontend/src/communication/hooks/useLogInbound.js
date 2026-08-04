import { useMutation, useQueryClient } from "@tanstack/react-query";

import { logInboundMessage } from "../services/communicationApi";

export function useLogInbound() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: logInboundMessage,
    onSuccess: (data) => {
      const jobId = data?.related_job_application_id;
      if (jobId) {
        queryClient.invalidateQueries({ queryKey: ["communicationThread", jobId] });
        queryClient.invalidateQueries({ queryKey: ["workspace", jobId] });
      }
      queryClient.invalidateQueries({ queryKey: ["communicationMessages"] });
    },
  });
}
