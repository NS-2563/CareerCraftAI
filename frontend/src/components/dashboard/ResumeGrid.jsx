import ResumeCard from "./ResumeCard";
import { createResumeActions } from "./resumeActions";

export default function ResumeGrid({ filteredResumes, formatDate, handlers }) {
  const {
    handleDuplicate,
    openRenameModal,
    handleViewVersions,
    handleArchive,
    handleRestore,
    handleDelete,
  } = handlers;

  const actions = createResumeActions({
  handleDuplicate,
  openRenameModal,
  handleViewVersions,
  handleArchive,
  handleRestore,
  handleDelete,
});

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {filteredResumes.map((resume) => (
        <ResumeCard
  key={resume.id}
  resume={resume}
  formatDate={formatDate}
  actions={actions}
/>
      ))}
    </div>
  );
}

