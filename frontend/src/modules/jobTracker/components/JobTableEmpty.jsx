import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function JobTableEmpty({ onCreate }) {
  return (
    <div className="flex items-center justify-center p-12">
      <div className="text-center">
        <div className="text-base font-medium">No job applications found</div>
        <div className="mt-2 text-sm text-muted-foreground">
          Add a job application to see it here.
        </div>
        {onCreate && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="mt-4 gap-1.5"
            onClick={onCreate}
          >
            <Plus className="size-4" />
            Add Job
          </Button>
        )}
      </div>
    </div>
  );
}
