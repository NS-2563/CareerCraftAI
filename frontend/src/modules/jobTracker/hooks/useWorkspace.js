import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import {
  getWorkspaceInsights,
  dismissWorkspaceInsight,
} from "../api/jobTrackerApi";

/**
 * Workspace header payload for one application: deterministic next action +
 * dismissible insight cards + dismissed keys.
 *
 * Query key "workspace" is invalidated by the module mutations (cover letter
 * generate, JD match re-check, message send) so the recommendation reflects
 * current completion state.
 */
export function useWorkspace(jobApplicationId, options = {}) {
  return useQuery({
    queryKey: ["workspace", jobApplicationId],
    queryFn: async () => {
      if (jobApplicationId === undefined || jobApplicationId === null) {
        return { next_action: null, insights: [], dismissed: [] };
      }
      const result = await getWorkspaceInsights(jobApplicationId);
      return result?.data ?? { next_action: null, insights: [], dismissed: [] };
    },
    enabled: jobApplicationId !== undefined && jobApplicationId !== null,
    retry: false,
    ...options,
  });
}

/**
 * Dismiss an insight card. On success the workspace query is refreshed so the
 * card disappears without a full reload.
 */
export function useDismissWorkspaceInsight(jobApplicationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (insightKey) => dismissWorkspaceInsight(jobApplicationId, insightKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspace", jobApplicationId] });
    },
  });
}
