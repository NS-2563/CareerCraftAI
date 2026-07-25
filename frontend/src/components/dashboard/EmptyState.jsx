import { FileText, SearchX, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function EmptyState({
  showArchived,
  searchQuery,
  activeFilter,
  onClearFilters,
  onImport,
}) {
  const hasActiveFilters = searchQuery || (activeFilter && activeFilter !== "all");

  if (hasActiveFilters) {
    return (
      <div className="bg-white rounded-xl border shadow-sm p-10 text-center">
        <div className="mx-auto mb-4 w-14 h-14 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
          <SearchX className="w-6 h-6 text-primary" />
        </div>
        <p className="text-gray-500 mb-2">No matching resumes</p>
        <p className="text-gray-600 mb-6">
          We couldn&apos;t find any resumes matching your current search or filters.
        </p>
        <Button variant="outline" onClick={onClearFilters}>
          Clear Search &amp; Filters
        </Button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border shadow-sm p-10 text-center">
      <div className="mx-auto mb-4 w-14 h-14 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
        <FileText className="w-6 h-6 text-primary" />
      </div>
      <p className="text-gray-500 mb-2">No resumes yet</p>
      <p className="text-gray-600 mb-6">Create your first resume to get started.</p>
      {!showArchived && (
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button asChild variant="outline">
            <a href="/resume-studio">Create Resume</a>
          </Button>
          <Button variant="outline" onClick={onImport}>
            <Upload className="w-4 h-4 mr-2" />
            Import Resume
          </Button>
        </div>
      )}
    </div>
  );
}



