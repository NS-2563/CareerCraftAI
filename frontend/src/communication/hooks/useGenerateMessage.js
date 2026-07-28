import { useMutation, useQueryClient } from "@tanstack/react-query";

import { generateMessage } from "../services/communicationApi";

export function useGenerateMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: generateMessage,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["communicationMessages"] });
    },
  });
}
