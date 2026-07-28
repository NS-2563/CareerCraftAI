import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getSuggestions, dismissSuggestion, generateFromSuggestion } from "@/communication/services/communicationApi";

export function useSuggestions() {
  return useQuery({
    queryKey: ["communicationSuggestions"],
    queryFn: getSuggestions,
    refetchInterval: 60_000,
    staleTime: 30_000,
    retry: false,
  });
}

export function useDismissSuggestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id) => dismissSuggestion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["communicationSuggestions"] });
    },
  });
}

export function useGenerateFromSuggestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id) => generateFromSuggestion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["communicationSuggestions"] });
      queryClient.invalidateQueries({ queryKey: ["communicationMessages"] });
    },
  });
}
