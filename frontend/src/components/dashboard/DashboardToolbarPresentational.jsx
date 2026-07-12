

// Pure presentational toolbar.
// This file is intentionally kept minimal and UI-only.

export default function DashboardToolbarPresentational({
  activeFilter,
  handleFilterChange,
  searchQuery,
  setSearchQuery,
  sortBy,
  setSortBy,
}) {
  return (
    <div className="flex flex-wrap items-center gap-3 border-b pb-4">
      <div className="flex items-center gap-3 flex-1">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search resumes..."
          className="w-full max-w-xs px-3 py-2 border rounded-md"
        />

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-3 py-2 border rounded-md"
        >
          <option value="updated_at">Sort: Updated</option>
          <option value="name">Sort: Name</option>
        </select>

        <select
          value={activeFilter}
          onChange={(e) => handleFilterChange(e.target.value)}
          className="px-3 py-2 border rounded-md"
        >
          <option value="all">Filter: Active</option>
          <option value="draft">Filter: Draft</option>
          <option value="completed">Filter: Completed</option>
          <option value="archived">Filter: Archived</option>
        </select>
      </div>

      <div className="ml-auto">
        <a
          href="/resume-studio?create=1"
          className="inline-flex items-center justify-center px-4 py-2 rounded-md bg-blue-600 text-white"
        >
          Create Resume
        </a>
      </div>
    </div>
  );
}





