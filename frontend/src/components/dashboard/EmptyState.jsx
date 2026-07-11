import { FileText } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function EmptyState({ showArchived }) {
  return (
    <div className="bg-white rounded-xl border shadow-sm p-10 text-center">
      <div className="mx-auto mb-4 w-14 h-14 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
        <FileText className="w-6 h-6 text-primary" />
      </div>
      <p className="text-gray-500 mb-2">No resumes yet</p>
      <p className="text-gray-600 mb-6">Create your first resume to get started.</p>
      {!showArchived && (
        <Button asChild variant="outline">
          <a href="/resume-studio">Create Resume</a>
        </Button>
      )}
    </div>
  );
}

