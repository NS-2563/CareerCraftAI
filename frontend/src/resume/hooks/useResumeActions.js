import { useCallback } from "react";
import { apiClient } from "@/lib/api";

export function useResumeActions({
  setResumes,
  setArchivedResumes,
  fetchResumes,
  setShowRenameModal,
  setRenameValue,
  setSelectedResume,
  setShowVersionModal,
  setVersions,
  selectedResume,
}) {
  // -------------------------
  // DELETE
  // -------------------------
  const handleDelete = useCallback(async (id) => {
    if (!confirm("Are you sure you want to delete this resume?")) return;

    try {
      await apiClient.delete(`/api/resume/${id}`);

      setResumes((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      console.error(err);
    }
  }, [setResumes]);

  // -------------------------
  // DUPLICATE
  // -------------------------
  const handleDuplicate = useCallback(async (resume) => {
    try {
      const res = await apiClient.post(
        `/api/resume/${resume.id}/duplicate`,
        {
          name: `${resume.name} (Copy)`,
        }
      );

      setResumes((prev) => [...prev, res.data]);
    } catch (err) {
      console.error(err);
    }
  }, [setResumes]);

  // -------------------------
  // ARCHIVE
  // -------------------------
  const handleArchive = useCallback(async (id) => {
    try {
      await apiClient.post(`/api/resume/${id}/archive`);
      setResumes((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      console.error(err);
    }
  }, [setResumes]);

  // -------------------------
  // RESTORE
  // -------------------------
  const handleRestore = useCallback(async (id) => {
    try {
      await apiClient.post(`/api/resume/${id}/restore`);
      setArchivedResumes((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      console.error(err);
    }
  }, [setArchivedResumes]);

  // -------------------------
  // RENAME
  // -------------------------
  const handleRename = useCallback(async (id, renameValue) => {
    if (!renameValue.trim()) return;

    try {
      await apiClient.post(`/api/resume/${id}/rename`, {
        name: renameValue,
      });

      setShowRenameModal(false);
      setRenameValue("");
      fetchResumes();
    } catch (err) {
      console.error(err);
    }
  }, [fetchResumes, setShowRenameModal, setRenameValue]);

  // -------------------------
  // VERSION HISTORY
  // -------------------------
  const handleViewVersions = useCallback(async (resume) => {
    setSelectedResume(resume);

    try {
      const res = await apiClient.get(
        `/api/resume/${resume.id}/versions`
      );

      setVersions(res.data || []);
      setShowVersionModal(true);
    } catch (err) {
      console.error(err);
    }
  }, [setSelectedResume, setVersions, setShowVersionModal]);

  // -------------------------
  // RESTORE VERSION
  // -------------------------
  const handleRestoreVersion = useCallback(async (versionNum) => {
    if (!confirm(`Restore version ${versionNum}?`)) return;

    try {
      await apiClient.post(
        `/api/resume/${selectedResume.id}/versions/${versionNum}/restore`,
        { version: versionNum }
      );

      setShowVersionModal(false);
      fetchResumes();
    } catch (err) {
      console.error(err);
    }
  }, [selectedResume, fetchResumes, setShowVersionModal]);

  return {
    handleDelete,
    handleDuplicate,
    handleArchive,
    handleRestore,
    handleRename,
    handleViewVersions,
    handleRestoreVersion,
  };
}

