import { useState, useMemo } from "react";

import DashboardToolbar from "@/components/dashboard/DashboardToolbar";
import ResumeGrid from "@/components/dashboard/ResumeGrid";
import EmptyState from "@/components/dashboard/EmptyState";
import VersionHistoryModal from "@/components/dashboard/VersionHistoryModal";
import RenameModal from "@/components/dashboard/RenameModal";
import { getVersions } from "@/resume/services/resumeApi";

import { useResumes } from "@/resume/hooks/useResumes";
import { useResumeMutations } from "@/resume/hooks/useResumeMutations";

export default function Dashboard() {
  // =========================
  // UI STATE ONLY
  // =========================
  const [activeFilter, setActiveFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("updated_at");

  const [showVersionModal, setShowVersionModal] = useState(false);
  const [selectedResume, setSelectedResume] = useState(null);
  const [versions, setVersions] = useState([]);

  const [showRenameModal, setShowRenameModal] = useState(false);
  const [renameValue, setRenameValue] = useState("");

  // =========================
  // DATA (REACT QUERY)
  // =========================
  const { data: resumes = [], isLoading } = useResumes(
  searchQuery,
  sortBy,
  activeFilter
);

  // =========================
  // MUTATIONS
  // =========================
  const {
    duplicate,
    archive,
    restore,
    remove,
    rename,
    restoreVersion,
  } = useResumeMutations();

  // =========================
  // FILTERING (CLIENT SIDE)
  // =========================
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

  // =========================
  // HANDLERS (WRAPPED MUTATIONS)
  // =========================
  const handleDuplicate = (resume) => {
  console.log("handleDuplicate", resume);
  duplicate.mutate({
    id: resume.id,
    name: `${resume.name} (Copy)`,
  });
};

  const handleArchive = (id) => archive.mutate(id);
  const handleRestore = (id) => restore.mutate(id);
  const handleDelete = (id) => remove.mutate(id);

  const handleRename = (id) => {
    rename.mutate({ id, name: renameValue });
    setShowRenameModal(false);
    setRenameValue("");
  };

  const handleRestoreVersion = (versionNum) => {
    restoreVersion.mutate({
      id: selectedResume.id,
      version: versionNum,
    });

    setShowVersionModal(false);
  };

  const openRenameModal = (resume) => {
    setSelectedResume(resume);
    setRenameValue(resume.name);
    setShowRenameModal(true);
  };

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

  // =========================
  // LOADING
  // =========================
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
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
      />

      {filteredResumes.length === 0 ? (
        <EmptyState showArchived={activeFilter === "archived"} />
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
    </div>
  );
}



