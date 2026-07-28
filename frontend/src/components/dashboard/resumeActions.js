export const createResumeActions = (actions) => {
  return [
    {
      label: "Edit",
      type: "link",
      group: "primary",
      variant: "ghost",
      href: (id) => `/resume-studio?id=${id}`,
    },
    {
      label: "Analyze",
      type: "link",
      group: "menu",
      href: (id) => `/resume?id=${id}`,
    },
    {
      label: "Duplicate",
      group: "menu",
      action: actions.handleDuplicate,
    },
    {
      label: "Rename",
      group: "menu",
      action: actions.openRenameModal,
    },
    {
      label: "Export",
      type: "link",
      group: "menu",
      href: (id) => `/resume-studio?id=${id}`,
    },
    {
      label: "History",
      group: "menu",
      action: actions.handleViewVersions,
    },
    {
      label: "Archive",
      group: "menu",
      action: actions.handleArchive,
      condition: (r) => r.is_archived === false,
    },
    {
      label: "Restore",
      group: "menu",
      action: actions.handleRestore,
      condition: (r) => r.is_archived === true,
    },
    {
      label: "Delete",
      group: "menu",
      action: actions.handleDelete,
      destructive: true,
    },
  ];
};

