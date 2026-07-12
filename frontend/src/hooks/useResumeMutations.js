import { useMutation, useQueryClient } from "@tanstack/react-query";
import resumeApi from "@/services/resumeApi";

export function useResumeMutations() {
  const queryClient = useQueryClient();

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["resumes"] });

  const duplicate = useMutation({
  mutationFn: ({ id, name }) =>
    resumeApi.duplicateResume(id, name),
  onSuccess: invalidate,
});

const archive = useMutation({
  mutationFn: resumeApi.archiveResume,
  onSuccess: invalidate,
});

const restore = useMutation({
  mutationFn: resumeApi.restoreResume,
  onSuccess: invalidate,
});

const remove = useMutation({
  mutationFn: resumeApi.deleteResume,
  onSuccess: invalidate,
});

const rename = useMutation({
  mutationFn: ({ id, name }) =>
    resumeApi.renameResume(id, name),
  onSuccess: invalidate,
});

const restoreVersion = useMutation({
  mutationFn: ({ id, version }) =>
    resumeApi.restoreVersion(id, version),
  onSuccess: invalidate,
});

  return {
  duplicate,
  archive,
  restore,
  remove,
  rename,
  restoreVersion,
};
}

