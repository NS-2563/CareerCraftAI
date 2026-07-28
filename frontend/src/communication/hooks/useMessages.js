import { useQuery } from "@tanstack/react-query";

import { getMessages } from "../services/communicationApi";

export function useMessages(params = {}) {
  return useQuery({
    queryKey: ["communicationMessages", params],
    queryFn: () => getMessages(params),
    retry: false,
  });
}
