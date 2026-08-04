import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import {
  getConversationStatus,
  setConversationStatus,
} from "../services/communicationApi";

export function useConversationStatus(jobApplicationId, options = {}) {
  return useQuery({
    queryKey: ["communicationConversationStatus", jobApplicationId],
    queryFn: () => getConversationStatus(jobApplicationId),
    enabled: jobApplicationId !== undefined && jobApplicationId !== null,
    retry: false,
    ...options,
  });
}

export function useSetConversationStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ jobApplicationId, status }) =>
      setConversationStatus(jobApplicationId, status),
    onSuccess: (_data, { jobApplicationId }) => {
      queryClient.invalidateQueries({
        queryKey: ["communicationConversationStatus", jobApplicationId],
      });
      queryClient.invalidateQueries({ queryKey: ["communicationThread", jobApplicationId] });
      queryClient.invalidateQueries({ queryKey: ["communicationMessages"] });
      queryClient.invalidateQueries({ queryKey: ["communicationConversationStatuses"] });
    },
  });
}
