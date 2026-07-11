export const createResumeActions = (actions) => {
  return [
    {
      label: "Edit",
      type: "link",
      variant: "ghost",
      href: (id) => `/resume-studio?id=${id}`,
    },
    {
      label: "Duplicate",
      action: actions.handleDuplicate,
      variant: "ghost",
    },
    {
      label: "Rename",
      action: actions.openRenameModal,
      variant: "ghost",
    },
    {
      label: "History",
      action: actions.handleViewVersions,
      variant: "ghost",
    },
    {
      label: "Archive",
      action: actions.handleArchive,
      condition: (r) => r.is_archived === false,
      variant: "outline",
    },
    {
      label: "Restore",
      action: actions.handleRestore,
      condition: (r) => r.is_archived === true,
      variant: "outline",
    },
    {
      label: "Delete",
      action: actions.handleDelete,
      variant: "destructive",
    },
  ];
};