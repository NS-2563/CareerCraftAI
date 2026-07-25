import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import resumeApi from "@/services/resumeApi";

function extractMessage(err) {
  const detail = err?.response?.data?.detail;
  if (detail) {
    if (typeof detail === "object" && detail.message) return detail.message;
    if (typeof detail === "string") return detail;
  }
  return null;
}

function showError(err, fallback) {
  const msg = extractMessage(err) || fallback;
  toast.error(msg);
}

export function useResumeMutations() {
  const queryClient = useQueryClient();

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["resumes"] });

  const duplicate = useMutation({
    mutationFn: ({ id, name }) => resumeApi.duplicateResume(id, name),
    onSuccess: () => {
      invalidate();
      toast.success("Resume duplicated");
    },
    onError: (err) => showError(err, "Failed to duplicate resume"),
  });

  const archive = useMutation({
    mutationFn: resumeApi.archiveResume,
    onSuccess: () => {
      invalidate();
      toast.success("Resume archived");
    },
    onError: (err) => showError(err, "Failed to archive resume"),
  });

  const restore = useMutation({
    mutationFn: resumeApi.restoreResume,
    onSuccess: () => {
      invalidate();
      toast.success("Resume restored");
    },
    onError: (err) => showError(err, "Failed to restore resume"),
  });

  const remove = useMutation({
    mutationFn: resumeApi.deleteResume,
    onSuccess: () => {
      invalidate();
      toast.success("Resume deleted permanently");
    },
    onError: (err) => showError(err, "Failed to delete resume"),
  });

  const rename = useMutation({
    mutationFn: ({ id, name }) => resumeApi.renameResume(id, name),
    onSuccess: () => {
      invalidate();
      toast.success("Resume renamed");
    },
    onError: (err) => showError(err, "Failed to rename resume"),
  });

  const restoreVersion = useMutation({
    mutationFn: ({ id, version }) => resumeApi.restoreVersion(id, version),
    onSuccess: () => {
      invalidate();
      toast.success("Version restored");
    },
    onError: (err) => showError(err, "Failed to restore version"),
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

