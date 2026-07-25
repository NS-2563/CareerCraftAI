
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Upload } from "lucide-react";

export default function DashboardToolbarPresentational({
  activeFilter,
  handleFilterChange,
  searchQuery,
  setSearchQuery,
  sortBy,
  setSortBy,
  onImport,
}) {
  return (
    <div className="flex flex-col gap-3 border-b pb-4">
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <Input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search resumes..."
          className="flex-1"
        />

        <Button variant="outline" onClick={onImport} className="shrink-0">
          <Upload className="w-4 h-4 mr-2" />
          Import
        </Button>

        <Button variant="default" asChild className="shrink-0">
          <a href="/resume-studio?create=1">Create Resume</a>
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="h-9 rounded-md border border-input bg-transparent px-2.5 py-1 text-sm shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          <option value="updated_at">Sort: Updated</option>
          <option value="name">Sort: Name</option>
        </select>

        <select
          value={activeFilter}
          onChange={(e) => handleFilterChange(e.target.value)}
          className="h-9 rounded-md border border-input bg-transparent px-2.5 py-1 text-sm shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          <option value="all">Filter: Active</option>
          <option value="draft">Filter: Draft</option>
          <option value="completed">Filter: Completed</option>
          <option value="archived">Filter: Archived</option>
        </select>
      </div>
    </div>
  );
}





