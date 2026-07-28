import { useState, useMemo, useCallback } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import DashboardToolbar from "@/components/dashboard/DashboardToolbar";
import ResumeGrid from "@/components/dashboard/ResumeGrid";
import EmptyState from "@/components/dashboard/EmptyState";
import VersionHistoryModal from "@/components/dashboard/VersionHistoryModal";
import RenameModal from "@/components/dashboard/RenameModal";
import DeleteConfirmModal from "@/components/ui/DeleteConfirmModal";
import ImportResumeModal from "@/components/dashboard/ImportResumeModal";
import { getVersions } from "@/services/resumeApi";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { useResumes } from "@/hooks/useResumes";
import { useResumeMutations } from "@/hooks/useResumeMutations";

export default function Dashboard() {
  const [activeFilter, setActiveFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("updated_at");

  const [showVersionModal, setShowVersionModal] = useState(false);
  const [selectedResume, setSelectedResume] = useState(null);
  const [versions, setVersions] = useState([]);

  const [showRenameModal, setShowRenameModal] = useState(false);
  const [renameValue, setRenameValue] = useState("");

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [showImportModal, setShowImportModal] = useState(false);

  const queryClient = useQueryClient();

  const { data: resumes = [], isLoading } = useResumes(searchQuery, sortBy, activeFilter);

  const {
    duplicate,
    archive,
    restore,
    remove,
    rename,
    restoreVersion,
  } = useResumeMutations();

  const filteredResumes = useMemo(() => {
    if (!resumes) return [];
    switch (activeFilter) {
      case "archived":
        return resumes.filter((r) => r.is_archived);
      case "draft":
        return resumes.filter((r) => !r.completed && !r.is_archived);
      case "completed":
        return resumes.filter((r) => r.completed && !r.is_archived);
      default:
        return resumes.filter((r) => !r.is_archived);
    }
  }, [resumes, activeFilter]);

  const handleDuplicate = (resume) => {
    if (!duplicate.isPending) {
      duplicate.mutate({ id: resume.id, name: `${resume.name} (Copy)` });
    }
  };

  const handleArchive = (id) => {
    if (!archive.isPending) archive.mutate(id);
  };
  const handleRestore = (id) => {
    if (!restore.isPending) restore.mutate(id);
  };

  const handleDelete = (id) => {
    const resume = resumes.find(r => r.id === id);
    if (resume) {
      setDeleteTarget(resume);
      setShowDeleteModal(true);
    }
  };

  const handleConfirmDelete = () => {
    if (deleteTarget && !remove.isPending) {
      remove.mutate(deleteTarget.id, {
        onSettled: () => {
          setShowDeleteModal(false);
          setDeleteTarget(null);
        },
      });
    }
  };

  const mutationStates = {
    archivePending: archive.isPending,
    restorePending: restore.isPending,
    deletePending: remove.isPending,
  };

  const handleRename = (id) => {
    if (!rename.isPending) {
      rename.mutate({ id, name: renameValue });
      setShowRenameModal(false);
      setRenameValue("");
    }
  };

  const handleRestoreVersion = (versionNum) => {
    if (!restoreVersion.isPending) {
      restoreVersion.mutate(
        { id: selectedResume.id, version: versionNum },
        { onSuccess: () => setShowVersionModal(false) }
      );
    }
  };

  const openRenameModal = (resume) => {
    setSelectedResume(resume);
    setRenameValue(resume.name);
    setShowRenameModal(true);
  };

  const handleImportSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["resumes"] });
    toast.success("Resume imported successfully");
  }, [queryClient]);

  const handleViewVersions = async (resume) => {
    try {
      setSelectedResume(resume);
      const data = await getVersions(resume.id);
      setVersions(Array.isArray(data) ? data : []);
      setShowVersionModal(true);
    } catch (err) {
      console.error("Failed to load version history:", err);
      setVersions([]);
    }
  };

  const formatDate = (d) =>
    d ? new Date(d).toLocaleDateString() : "N/A";

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Skeleton className="h-9 w-full sm:w-80" />
          <Skeleton className="h-9 w-32" />
          <Skeleton className="h-9 w-28" />
          <Skeleton className="h-9 w-28" />
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="rounded-xl border p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <Skeleton className="h-5 w-40" />
                <Skeleton className="h-8 w-8 rounded-md" />
              </div>

              <div className="flex gap-2">
                <Skeleton className="h-5 w-20" />
                <Skeleton className="h-5 w-16" />
              </div>

              <Skeleton className="h-px w-full" />
              <Skeleton className="h-4 w-36" />
              <Skeleton className="h-9 w-full" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <DashboardToolbar
        activeFilter={activeFilter}
        handleFilterChange={setActiveFilter}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        sortBy={sortBy}
        setSortBy={setSortBy}
        onImport={() => setShowImportModal(true)}
      />

      {filteredResumes.length === 0 ? (
        <EmptyState
          showArchived={activeFilter === "archived"}
          searchQuery={searchQuery}
          activeFilter={activeFilter}
          onClearFilters={() => {
            setSearchQuery("");
            setActiveFilter("all");
          }}
          onImport={() => setShowImportModal(true)}
        />
      ) : (
        <ResumeGrid
          filteredResumes={filteredResumes}
          formatDate={formatDate}
          handlers={{
            handleDuplicate,
            openRenameModal,
            handleViewVersions,
            handleArchive,
            handleRestore,
            handleDelete,
          }}
          mutationStates={mutationStates}
        />
      )}

      <VersionHistoryModal
        showVersionModal={showVersionModal}
        versions={versions}
        handleClose={() => setShowVersionModal(false)}
        handleRestoreVersion={handleRestoreVersion}
      />

      <RenameModal
        showRenameModal={showRenameModal}
        renameValue={renameValue}
        setRenameValue={setRenameValue}
        handleRename={handleRename}
        selectedResume={selectedResume}
        handleClose={() => setShowRenameModal(false)}
      />

      <DeleteConfirmModal
        open={showDeleteModal}
        title={deleteTarget ? `Delete "${deleteTarget.name}"` : "Delete Resume"}
        description={
          deleteTarget
            ? `Are you sure you want to delete "${deleteTarget.name}"? This action cannot be undone. All version history will be permanently removed.`
            : "Are you sure you want to delete this resume? This action cannot be undone."
        }
        onCancel={() => {
          setShowDeleteModal(false);
          setDeleteTarget(null);
        }}
        onConfirm={handleConfirmDelete}
        confirmDisabled={remove.isPending}
      />

      <ImportResumeModal
        open={showImportModal}
        onClose={() => setShowImportModal(false)}
        onSuccess={handleImportSuccess}
      />
    </div>
  );
}
