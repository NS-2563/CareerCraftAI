import { useMutation, useQueryClient } from "@tanstack/react-query";

import { deleteMessage } from "../services/communicationApi";

export function useDeleteMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteMessage,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["communicationMessages"] });
    },
  });
}
